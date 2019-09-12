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

def lot_size(assetQ, stepSize):
    fix_size = assetQ % stepSize
    return assetQ - fix_size

def monitor(*args):
    print(f"{' bot_stablecoin_binance ':-^35}")
    print(f"{ctime():-^35}")
    print(f"Binance {coin}: {coinB:.2f} {asset}: {assetB:.2f}")

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
    if k['symbol'] == 'TUSDUSDT':
        for j in k['filters']:
            if j['filterType'] == 'LOT_SIZE':
                minQty = float(j['minQty'])
                maxQty = float(j['maxQty'])
                stepSize = float(j['stepSize'])

# define spread and last price
spread = taker
last_price = 0.9988

#trade
while True:
    try:
        # check balances
        coinB, assetB = get_balance(coin,asset, client.rBalances())
        monitor(coin,asset,coinB,assetB)
        if coinB > assetB:
            while True:
                price_ask, assetQ, coin_total = mean_asks_price(coinB,assetB,client.rOrderBook(symbol,10,'asks'))
                if price_ask < last_price and assetQ * (1 - spread) > coinB:
                    # buy asset
                    fixQ = lot_size(assetQ, stepSize)
                    response = client.marketBuy(symbol, fixQ)
                    last_price = price_ask
                    break
                sleep(1)
        elif assetB > coinB:
            while True:
                price_bid, coinQ, asset_total = mean_bids_price(coinB,assetB,client.rOrderBook(symbol,10,'bids'))
                if price_bid > last_price and coinQ * (1 - spread) > assetB:
                    # sell asset
                    fixQ = lot_size(asset_total, stepSize)
                    response = client.marketSell(symbol, fixQ)
                    last_price = price_bid
                    break
                sleep(1)
        # trade history
        if response is not None:
            data = open('trade_history.txt','a+')
            data.write(f'{response}\n')
    except KeyboardInterrupt:
        print('\nSTOPED BY USER')
        print(last_price)
        break
    except Exception as e:
        print(str(e))
