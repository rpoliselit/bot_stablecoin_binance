import arbitration_bot
from time import perf_counter

if __name__ == '__main__':
    start = perf_counter()
    arbitration_bot.main()
    elapse = perf_counter() - start
    print(f'Total running time: {elapse:.1f} secunds')
