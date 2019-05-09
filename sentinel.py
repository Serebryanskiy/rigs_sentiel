from datetime import datetime
from urllib.request import Request, urlopen
from urllib import error
import inspect
import json
import mysql.connector
import time
from bs4 import BeautifulSoup
from config import config
from timer import set_interval


class Connections:
    connection = mysql.connector.connect(user=config['sql']['user'], password=config['sql']['password'],
                                         host=config['sql']['host'],
                                         database=config['sql']['database'],
                                         auth_plugin='mysql_native_password')
    cursor = connection.cursor()

    def get_json(self, url, raw=False):
        headers = config["headers"].copy()
        headers.pop('Content-Type')
        request_form = Request(url=url, headers=headers)
        try:
            output = (urlopen(request_form), False) if raw else (json.loads(urlopen(request_form).read()), False)
        except error.HTTPError as err:
            output = (err.msg, url, headers), True
        except error.URLError as err:
            output = (err, f'url: {url}'), True

        return output

    def log(self, string):
        print(f'[{datetime.now().strftime("%d/%m/%y %H:%M:%S.%f")[:-3]}] {string}')


class Coin(Connections):
    def __init__(self, coin):
        self.coin = coin

    def get_balance(self):
        coins = config['coins']

        if self.coin == 'XZC':
            response, err = self.get_json(coins[self.coin]['pool_balance'] + coins[self.coin]['wallet'])
            if err is not True:
                total = sum(response['miner']['balances'].values())

        if self.coin == 'BIS2':
            response, err = self.get_json(coins[self.coin]['pool_balance'] + coins[self.coin]['wallet'])
            if err is not True:
                total = response['BIS']['total_paid'] + response['BIS']['balance'] + response['BIS']['immature']

        if self.coin == 'BIS':
            response, err = self.get_json(coins[self.coin]['pool_balance'] + coins[self.coin]['wallet'], raw=True)
            if err is not True:
                soup = BeautifulSoup(response, 'html.parser')
                table = soup.find('table', attrs={'class': 'dataGrid2'})
                for element in table:
                    if str(element).find('Total Earned') >= 0:
                        total_str = element.find_all('td')[3].text
                        total = float(total_str[:-4])
        if self.coin == 'NIM':
            response, err = self.get_json(coins[self.coin]['pool_balance'] + coins[self.coin]['wallet'])
            if err is not True:
                total = response['total_income'] / 100000

        return (total, err) if err is not True else (response, err)

    def insert_miner_stats(self):
        balance, err = self.get_balance()
        if err is not True:
            now = datetime.now()
            add_stat = ("INSERT INTO miner_stats "
                        "VALUES (%(date)s, %(coin)s, %(balance)s)")
            data_stat = {
                "date": now,
                "coin": self.coin,
                "balance": balance,
            }
            self.cursor.execute(add_stat, data_stat)
            self.connection.commit()
        else:
            self.log(f'Error: {balance} occured while trying to use {inspect.stack()[0][3]}')

    def get_revenue(self, local_json, cointomine_db):
        shift = 60 * 60 * 12 + 60 * 10  # 12 hours - 5 minute
        now_12_shift = datetime.now().timestamp() - shift
        date = datetime.fromtimestamp(now_12_shift)
        query = ("SELECT * FROM miner_stats "
                 "WHERE date > %s and coin = %s")
        self.cursor.execute(query, (date, self.coin))
        response = [a for a in self.cursor]
        bitcoin_price = int(float(local_json['data']['ad_list'][10]['data']['temp_price']))
        coin_price = float(cointomine_db[self.coin]['bid_btc'])
        total_speed = sum(
            [value * config["coins"][self.coin]["benchmarks"][key] for key, value in config["rig"].items()])
        expected_revenue = int(float(
            cointomine_db[self.coin]['rewards_for_1mhs_avg24h']) * total_speed * coin_price * bitcoin_price / 2)
        expected_reward = round(int(float(
            cointomine_db[self.coin]['rewards_for_1mhs_avg24h']) * total_speed / 2), 2)

        if len(response) > 0:
            balance0 = float(response[0][2])
            balance1 = float(response[-1][2])

            coins_yield = round(balance1 - balance0, 5)

            revenue = int(coins_yield * coin_price * bitcoin_price)

            data = {
                "date": datetime.now(),
                "coin": self.coin,
                "revenue": revenue,
                "coin_revenue": coins_yield,
                "price": coin_price,
                "expected_revenue": expected_revenue,
                "expected_coins": expected_reward,
                "ratio": revenue / expected_revenue if expected_revenue != 0 else 0,

            }

            insert_string = ("INSERT INTO revenue "
                             "VALUES (%(date)s, %(coin)s, %(revenue)s, %(expected_revenue)s, %(ratio)s)")

            self.cursor.execute(insert_string, data)
            self.connection.commit()

            return data
        else:
            return {"revenue": 0, "expected_revenue": expected_revenue}


class HiveApi(Connections):
    def __init__(self, coins_list):
        self.base_url = config["hive"]["base_url"]
        self.auth = config["hive"]["auth"]
        self.set_token()
        self.farm_id = config["hive"]["farm_id"]

        self.telegram_token = config["telegram"]["token"]
        self.telegram_chat_id = config["telegram"]["chat_id"]
        self.coins = {}
        for coin_element in coins_list:
            self.coins[coin_element] = Coin(coin_element)

    def api_request(self, path, data=None):
        headers = config["headers"].copy()

        if hasattr(self, 'token') and path != '/auth/login':
            if datetime.now().timestamp() + 10 >= self.full_token['expires_in']:
                self.set_token()
            headers['Authorization'] = 'Bearer ' + self.token
        try:
            if data:
                request_form = Request(url=self.base_url + path, headers=headers, data=json.dumps(data).encode('utf-8'))
            else:
                request_form = Request(url=self.base_url + path, headers=headers)
            return json.loads(urlopen(request_form).read()), False
        except error.HTTPError as err:
            return err.msg, True
        except error.URLError as err:
            return (err, f'url: {self.base_url + path}'), True

    def set_token(self):
        response, err = self.api_request('/auth/login', self.auth)
        if err is not True:
            self.full_token = response
            self.full_token['expires_in'] += datetime.now().timestamp()
            self.token = self.full_token['access_token']
            self.log('New token received')
        else:
            self.log(f'Error: {response} while trying to use {inspect.stack()[0][3]}')

    def insert_rigs_stats(self):
        workers, err = self.api_request('/farms/' + self.farm_id + '/workers')
        if err is not True:
            now = datetime.now()
            add_stat = ("INSERT INTO rig_stats "
                        "VALUES (%(rigs_id)s, %(date)s, %(gpus_offline)s, %(online)s, %(hash)s, %(coin)s,%(power_draw)s)")
            for rig in workers["data"]:
                try:
                    data_stat = {
                        "rigs_id": rig["id"],
                        "date": now,
                        "gpus_offline": rig["stats"]["gpus_offline"],
                        "online": rig["stats"]["online"],
                        "hash": rig["miners_summary"]["hashrates"][0]["hash"],
                        "coin": rig["miners_summary"]["hashrates"][0]["coin"],
                        "power_draw": rig["stats"]["power_draw"] if hasattr(rig["stats"], "power_draw") else 0
                    }
                    self.cursor.execute(add_stat, data_stat)
                    self.connection.commit()
                except KeyError or IndexError as err:
                    self.log(err)

                if rig["stats"]["online"] is not True:
                    self.telegram_message(f'Mayday! Mayday! {rig["name"]} rig down, call for evac!')
                elif hasattr(rig, "miners_stats") and (
                        [True for gpu_temp in rig["miners_stats"]["hashrates"][0]['temps'] if gpu_temp == 0] or
                        data_stat['gpus_offline']):
                    bot_message = ['GPUs down:']
                    for i, gpu_temp in enumerate(rig["miners_stats"]["hashrates"][0]['temps']):
                        if gpu_temp == 0:
                            bot_message.append(f"{str(rig['gpu_info'][i]['bus_number'])} {rig['gpu_info'][i]['model']}")
                    self.telegram_message(f'{" | ".join(bot_message)}. Trying to reboot')
                    self.api_request(f'/farms/{self.farm_id}/workers/{data_stat["rigs_id"]}/command',
                                     {"command": "exec", "data": {"cmd": "sreboot wakealarm 120"}})
                    self.log('GPUs reactivation initiated')
                    time.sleep(60 * 5)
                    repeat_request, err = self.api_request(f'/farms/{self.farm_id}/workers/{rig["id"]}')
                    if err or (hasattr(rig, "miners_stats") and (
                            [True for gpu_temp in rig["miners_stats"]["hashrates"][0]['temps'] if gpu_temp == 0] or
                            data_stat['gpus_offline'])):
                        if err:
                            self.telegram_message(f'Failed to reactivate GPUs due api request failure')
                        else:
                            self.telegram_message(f'Failed to reactivate GPUs')
                    else:
                        self.telegram_message(f'Rebooted successfully, GPUs reactivated')

        else:
            self.log(f'Error occured while trying to use {inspect.stack()[0][3]}')

    def report(self):
        local_json, local_err = self.get_json(
            'https://localbitcoins.net/buy-bitcoins-online/RUB/transfers-with-specific-bank/.json')
        cointomine_db, cointomine_err = self.get_json('https://api.cointomine.today/api/v1/data')

        if local_err:
            self.log(f'Error in getting bitcoin price via localbitcoins: {local_json}')
        elif cointomine_err:
            self.log(f'Error in getting coins db via cointomine: {cointomine_db}')
        else:
            revenue_dict = {}
            for name, coin in self.coins.items():
                revenue_dict[name] = coin.get_revenue(local_json, cointomine_db)
            revenue = sum([value["revenue"] for value in revenue_dict.values()])
            now = datetime.now()
            data = {
                "date": now,
                "revenue": revenue,
                "bitcoin_revenue": round(revenue / float(local_json['data']['ad_list'][10]['data']['temp_price']), 8),
                "electricity_costs": config["electricity_costs"],
                "profit": revenue - config["electricity_costs"],
                "revenue_string": ','.join(
                    [f'{value["coin_revenue"]} {key} {value["revenue"]} RUB price {value["price"]}'
                     for key, value in revenue_dict.items() if value["revenue"] != 0]),
                "expected_string": ','.join(
                    [f'{key} : {value["expected_revenue"]}' for key, value in revenue_dict.items()])
            }

            insert_string = ("INSERT INTO report "
                             "VALUES (%(date)s, %(bitcoin_revenue)s, %(revenue)s, %(electricity_costs)s, %(profit)s)")

            self.cursor.execute(insert_string, data)
            self.connection.commit()

            self.telegram_message(f'Выручка: {data["revenue"]} р.\nЭлектричество: {data["electricity_costs"]} р.\n'
                                  f'Прибыль: {data["profit"]}, \nMined {data["revenue_string"]},\n'
                                  f'Calculated: {data["expected_string"]}')

    def telegram_message(self, message):
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0",
            "Content-Type": 'application/json'}
        data = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": 'Markdown'
        }
        url = 'https://api.telegram.org/bot' + self.telegram_token + '/sendMessage'
        request_form = Request(url=url, headers=headers, data=json.dumps(data).encode('utf-8'))
        try:
            urlopen(request_form)
        except error.HTTPError as err:
            response = err.read()
            self.log(f'telegram api error: url: {url}, err: {err.msg}, data: {response}')
        except error.URLError as err:
            self.log(f'telegram api error: {err}, url: {url}')


def rigs_bot():
    if 'hive_client' not in globals():
        global hive_client
        hive_client = HiveApi(coin_list)
    hive_client.insert_rigs_stats()
    for coin in hive_client.coins.values():
        coin.insert_miner_stats()
    if datetime.now().hour in config["report_hours"]:
        hive_client.report()
    hive_client.log('DB updated successfully')


coin_list = ['NIM', 'BIS', 'XZC', ]
if config["update_on_start"]:
    rigs_bot()
time_now = datetime.now()
start = time_now.replace(hour=time_now.hour + 1, minute=5, second=0, microsecond=0).strftime("%d/%m/%y %H:%M:%S")
set_interval(start, 60 * 60, rigs_bot)
# start can be replaced with a date in "30/12/19 8:00:00" format, otherwise will start at the beginning of next hour
