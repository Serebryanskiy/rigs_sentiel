from collections import namedtuple

Config = namedtuple('Config', 'sql, coins, hive, telegram, headers')

config = {
    "update_on_start": True,
    "report_hours": [8, 20],  # hours when reporting is done
    "rig": {"1070": 2, "1070ti": 2, "1080ti": 7},  # change
    "electricity_costs": int(2.5 * 2.4 * 12),  # kW/h, kw/h/rub, hours | change
    "coins": {
        "XZC": {
            "pool_balance": 'https://api.mintpond.com/v1/zcoin/miner/balances/',
            "wallet_balance": 'https://api.mintpond.com/v1/zcoin/miner/balances/',
            "wallet": 'a1RgSvUK2VmDD2ZHVPHb3snBGNZ2nHT6dx',  # change
            "benchmarks": {"1070": 2.285, "1070ti": 2.665, "1080ti": 3.400}},  # everywhere in Mh/s
        "BIS2": {
            "pool_balance": 'https://eggpool.net/index.php?action=api&miner=',
            "wallet": '09a84dd456bb85ee81c61fce2d166992b712f1f5246c773bc2b2e7e5'},  # change
        "BIS": {
            "pool_balance": 'https://www.noncepool.com/site/wallet_results?address=',
            "wallet_balance": 'http://bismuth.online/api/address/',
            "wallet": '09a84dd456bb85ee81c61fce2d166992b712f1f5246c773bc2b2e7e5',  # change
            "benchmarks": {"1070": 1270, "1070ti": 1515, "1080ti": 2040}},
        "NIM": {
            "pool_balance": 'https://api.sushipool.com/api/v1/stats/profile/',
            "wallet_balance": 'https://api.mintpond.com/v1/zcoin/miner/balances/',
            "wallet": 'NQ13 FK0X EREQ 5196 TP9R JP07 DNUM 7XDQ 457K',  # change
            "benchmarks": {"1070": 0.2060, "1070ti": 0.2075, "1080ti": 0.3285}}},
    "sql": {
        "host": '127.0.0.1',
        "user": "silver",
        "password": "demo666",
        "database": "rigs"},
    "hive": {"base_url": 'https://api2.hiveos.farm/api/v2',
             "auth": {'login': 'silver166', 'password': 'demo666'},  # change
             "farm_id": '126184'},  # change
    "telegram": {"token": '854945908:AAFunsj1ubO1-QtvVoTmV7By67yZxKIPupc',
                 "chat_id": '402540754'},  # post a message to @ceptor_bot in telegram
    "headers": {
        'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:66.0) Gecko/20100101 Firefox/66.0",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Content-Type": 'application/json'}

}
