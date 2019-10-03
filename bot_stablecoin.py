from time import sleep, ctime
from binanceAPI import binance
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

def truncate(num, decimal=0):
    from math import floor
    decimal = 10 ** decimal
    return floor(num * decimal) / decimal

def lot_size(asset_qty, stepSize):
    fix_size = asset_qty % stepSize
    return truncate(asset_qty - fix_size, 5)

def monitor(*args):
    print(f"{' bot_stablecoin_binance ':-^35}")
    print(f"{ctime():-^35}")
    print(f"Binance {coin}: {coin_bal:.8f} {asset}: {asset_bal:.8f}")

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
        coin_bal, asset_bal = get_balance(coin, asset, client.rBalances())
        monitor(coin,asset,coin_bal,asset_bal)
        if coin_bal > asset_bal:
            while True:
                price_ask, asset_qty, coin_total = mean_asks_price(coin_bal,asset_bal,client.rOrderBook(symbol,10,'asks'))
                if asset_qty * (1 - spread) > coin_total and lastprice > price_ask:
                    # buy asset
                    fixQ = lot_size(asset_qty, stepSize)
                    response = client.marketBuy(symbol, fixQ)
                    lastprice = price_ask
                    break
                sleep(1)
        elif asset_bal > coin_bal:
            while True:
                price_bid, coin_qty, asset_total = mean_bids_price(coin_bal,asset_bal,client.rOrderBook(symbol,10,'bids'))
                if coin_qty * (1 - spread) > asset_total and lastprice < price_bid:
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
