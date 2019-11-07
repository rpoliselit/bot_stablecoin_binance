import arbitration_bot
from time import perf_counter, strftime, gmtime

if __name__ == '__main__':
    start = perf_counter()
    arbitration_bot.main()
    elapsed = perf_counter() - start
    time_format = strftime("%H:%M:%S", gmtime(elapsed))
    print(f'Total running time: {time_format}')
