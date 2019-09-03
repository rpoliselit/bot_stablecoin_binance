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

def monitor(*args):
    print(f"{ctime():-^35}")
    print(f"Binance {coin}: {coinB:.2f} {asset}: {assetB:.2f}")

# binance client
client = binance(keys.binance_apikey, keys.binance_secret)
taker = 0.1 / 100

# currency pair of stable coin
coin = 'TUSD'
asset = 'USDC'
symbol = f'{asset}{coin}'

# define spread
spread = 0.2 / 100

# define initial balance
coinB, assetB = 100.0, 0

# trade
while True:
    try:
        monitor(coin,asset,coinB,assetB)
        if coinB != 0:
            while True:
                price_ask, assetQ, coin_total = mean_asks_price(coinB,assetB,client.rOrderBook(symbol,10,'asks'))
                if price_ask <= 1 - spread:
                    # buy asset
                    coinB -= coin_total
                    assetB += assetQ * (1 - taker)
        elif assetB !=0:
            while True:
                price_bid, coinQ, asset_total = mean_bids_price(coinB,assetB,client.rOrderBook(symbol,10,'bids'))
                if price_bid >= 1 + spread:
                    # sell asset
                    coinB += coinQ * (1 - taker)
                    assetB -= asset_total
    except KeyboardInterrupt:
        print('\nSTOPED BY USER')
        break
    except Exception as e:
        print(str(e))