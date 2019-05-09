import time
from datetime import datetime


def set_interval(start, period, f, *args):
    """
    Timer with a specific start date. Repeats passed function with arguments every n seconds.
    Example: set_interval("11/04/19 13:11:25", 10, hello)
    :param start: Date:time to start timer in %d/%m/%y %H:%M:%S format
    :param period: timer period in seconds
    :param f: function to invoke as timer triggers
    :param args: args of the function
    """
    time_tuple = time.strptime(start, "%d/%m/%y %H:%M:%S")
    start_time = time.mktime(time_tuple)
    print(f'[{datetime.now().strftime("%d/%m/%y %H:%M:%S.%f")[:-3]}] Timer start set to {start}')

    def g_tick():
        count = 0
        yield start_time - time.time()
        while True:
            count += 1
            yield max(start_time + count * period - time.time(), 0)

    g = g_tick()
    while True:
        time.sleep(next(g))
        f(*args)
