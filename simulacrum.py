from time import sleep, ctime
from binance_api import binance
import keys

def mean_asks_price(coin_qty, asset_qty, asks):
    try:
        coin_init = coin_qty
        for c in asks:
            if coin_qty > c[0] * c[1]:
                coin_qty -= c[0] * c[1]
                asset_qty += c[1]
            if coin_qty < c[0] * c[1]:
                asset_qty += coin_qty / c[0]
                coin_qty -= coin_qty
            if coin_qty == 0:
                break
    except:
        print(asks)
    else:
        return coin_init / asset_qty, asset_qty, coin_init

def mean_bids_price(coin_qty, asset_qty, bids):
    try:
        asset_init = asset_qty
        for c in bids:
            if asset_qty > c[1]:
                asset_qty -= c[1]
                coin_qty += c[0] * c[1]
            if asset_qty < c[1]:
                coin_qty += c[0] * asset_qty
                asset_qty -= asset_qty
            if asset_qty == 0:
                break
    except:
        print(bids)
    else:
        return coin_qty / asset_init, coin_qty, asset_init

def get_balance(coin, asset, balance):
    for c, k in enumerate(balance):
        if k['asset'] == coin:
            coin_bal_bin = float(k['free'])
        elif k['asset'] == asset:
            asset_bal_bin = float(k['free'])
    return coin_bal_bin, asset_bal_bin

def monitor(*args):
    print(f"{ctime():-^35}")
    print(f"Binance {coin}: {coin_bal:.2f} {asset}: {asset_bal:.2f}")

# binance client
client = binance(keys.binance_apikey, keys.binance_secret)
taker = 0.1 / 100

# currency pair of stable coin
coin = 'USDT'
asset = 'TUSD'
symbol = f'{asset}{coin}'

# define spread and last price
spread = taker
last_price = 1

# define initial balance
coin_bal, asset_bal = 100.0, 0

# trade simulation
while True:
    try:
        monitor(coin,asset,coin_bal,asset_bal)
        if coin_bal != 0:
            while True:
                price_ask, asset_qty, coin_total = mean_asks_price(coin_bal,asset_bal,client.rOrderBook(symbol,10,'asks'))
                if price_ask < last_price and asset_qty * (1 - spread) > coin_total:
                    # buy asset
                    coin_bal -= coin_total
                    asset_bal += asset_qty * (1 - taker)
                    break
                sleep(1)
        elif asset_bal !=0:
            while True:
                price_bid, coin_qty, asset_total = mean_bids_price(coin_bal,asset_bal,client.rOrderBook(symbol,10,'bids'))
                if price_bid > last_price and coin_qty * (1 - spread) > asset_total:
                    # sell asset
                    coin_bal += coin_qty * (1 - taker)
                    asset_bal -= asset_total
                    break
                sleep(1)
    except KeyboardInterrupt:
        print('\nSTOPED BY USER')
        break
    except Exception as e:
        print(str(e))
