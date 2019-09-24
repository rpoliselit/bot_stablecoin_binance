from time import sleep, ctime
from binanceAPI import binance
import keys

def mean_asks_price(coinQ, assetQ, asks):
    try:
        coinQ_init = coinQ
        for c in asks:
            if coinQ > c[0] * c[1]:
                coinQ -= c[0] * c[1]
                assetQ += c[1]
            if coinQ < c[0] * c[1]:
                assetQ += coinQ / c[0]
                coinQ -= coinQ
            if coinQ == 0:
                break
    except:
        print(asks)
    else:
        return coinQ_init / assetQ, assetQ, coinQ_init

def mean_bids_price(coinQ, assetQ, bids):
    try:
        assetQ_init = assetQ
        for c in bids:
            if assetQ > c[1]:
                assetQ -= c[1]
                coinQ += c[0] * c[1]
            if assetQ < c[1]:
                coinQ += c[0] * assetQ
                assetQ -= assetQ
            if assetQ == 0:
                break
    except:
        print(bids)
    else:
        return coinQ / assetQ_init, coinQ, assetQ_init

def get_balance(coin, asset, balance):
    for c, k in enumerate(balance):
        if k['asset'] == coin:
            coinB_bin = float(k['free'])
        elif k['asset'] == asset:
            assetB_bin = float(k['free'])
    return coinB_bin, assetB_bin

def truncate(num, decimal=0):
    from math import floor
    decimal = 10 ** decimal
    return floor(num * decimal) / decimal

def lot_size(assetQ, stepSize):
    fix_size = assetQ % stepSize
    return truncate(assetQ - fix_size, 5)

def monitor(*args):
    print(f"{' bot_stablecoin_binance ':-^35}")
    print(f"{ctime():-^35}")
    print(f"Binance {coin}: {coinB:.8f} {asset}: {assetB:.8f}")

# binance client
client = binance(keys.binance_apikey, keys.binance_secret)
taker = 0.1 / 100

# currency pair of stable coin
coin = 'USDT'
asset = 'TUSD'
symbol = f'{asset}{coin}'

# check lot_size
symbols = client.eInfo()['symbols']
for k in symbols:
    if k['symbol'] == symbol:
        for j in k['filters']:
            if j['filterType'] == 'LOT_SIZE':
                minQty = float(j['minQty'])
                maxQty = float(j['maxQty'])
                stepSize = float(j['stepSize'])

# define spread
spread = taker * 1.1
lastprice = 1
#trade
while True:
    try:
        # check balances
        coinB, assetB = get_balance(coin,asset, client.rBalances())
        monitor(coin,asset,coinB,assetB)
        if coinB > assetB:
            while True:
                price_ask, assetQ, coin_total = mean_asks_price(coinB,assetB,client.rOrderBook(symbol,10,'asks'))
                if assetQ * (1 - spread) > coin_total and lastprice > price_ask:
                    # buy asset
                    fixQ = lot_size(assetQ, stepSize)
                    response = client.marketBuy(symbol, fixQ)
                    lastprice = price_ask
                    break
                sleep(1)
        elif assetB > coinB:
            while True:
                price_bid, coinQ, asset_total = mean_bids_price(coinB,assetB,client.rOrderBook(symbol,10,'bids'))
                if coinQ * (1 - spread) > asset_total and lastprice < price_bid:
                    # sell asset
                    fixQ = lot_size(asset_total, stepSize)
                    response = client.marketSell(symbol, fixQ)
                    lastprice = price_bid
                    break
                sleep(1)
        # trade history
        if response is not None:
            data = open('trade_history.txt','a+')
            data.write(f'{response}\n')
            print(f"lastprice = {lastprice:.5f}")
    except KeyboardInterrupt:
        print('\nSTOPED BY USER')
        break
    except Exception as e:
        print(str(e))
