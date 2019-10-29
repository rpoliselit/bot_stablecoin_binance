from time import sleep, ctime
from binance_api import binance
from math import floor
import keys

def monitor(func):
    def balances(coin, asset, balance):
        coin_bal, asset_bal = func(coin, asset, balance)
        print(f"{' bot_stablecoin_binance ':-^35}")
        print(f"{ctime():-^35}")
        print(f"Binance {coin}: {coin_bal:.8f} {asset}: {asset_bal:.8f}")
        return coin_bal, asset_bal
    return balances

@monitor
def get_balance(coin, asset, all_balances):
    for balance in all_balances:
        if balance['asset'] == coin:
            coin_balance = float(balance['free'])
        elif balance['asset'] == asset:
            asset_balance = float(balance['free'])
    return coin_balance, asset_balance

def create_symbol(coin, asset):
    return f'{asset}{coin}'

def stepsize(symbol, client):
    all_markets = client.eInfo()['symbols']
    for market in all_markets:
        if market['symbol'] == symbol:
            for filter in market['filters']:
                if filter['filterType'] == 'LOT_SIZE':
                    # min_qty = float(filter['minQty'])
                    # max_qty = float(filter['maxQty'])
                    step_size = float(filter['stepSize'])
    return step_size

def mean_asks_price(coin_qty, asks):
    asset_qty = 0
    coin_init = coin_qty
    for ask in asks:
        ask_asset = ask[1] # asset quantity of an ask
        ask_price = ask[0] # price of each asset of an ask
        ask_coin = ask_price * ask_asset # total value in coin of an ask
        if coin_qty >= ask_coin:
            coin_qty -= ask_coin
            asset_qty += ask_asset
        elif coin_qty < ask_coin:
            asset_qty += coin_qty / ask_price
            coin_qty -= coin_qty
        elif coin_qty == 0:
            break
    mean_price = coin_init / asset_qty
    return mean_price, asset_qty

def mean_bids_price(asset_qty, bids):
    coin_qty = 0
    asset_init = asset_qty
    for bid in bids:
        bid_asset = bid[1] # asset quantity of a bid
        bid_price = bid[0] # price of each asset of a bid
        bid_coin = bid_price * bid_asset # total value in coin of a bid
        if asset_qty >= bid_asset:
            asset_qty -= bid_asset
            coin_qty += bid_coin
        elif asset_qty < bid_asset:
            coin_qty += bid_price * asset_qty
            asset_qty -= asset_qty
        elif asset_qty == 0:
            break
    mean_price = coin_qty / asset_init
    return mean_price, coin_qty

def truncate(num, decimal=0):
    decimal = 10 ** decimal
    return floor(num * decimal) / decimal

def lot_size(asset_qty, step_size):
    fix_size = asset_qty % step_size
    return truncate(asset_qty - fix_size, 5)

def automated_trade(coin, asset, client, last_price):
    coin_bal , asset_bal = get_balance(coin, asset, client.rBalances())
    taker = client.rTaker()
    symbol = create_symbol(coin,asset)
    step_size = stepsize(symbol,client)
    buying_asset = coin_bal > asset_bal
    selling_asset = coin_bal < asset_bal
    if buying_asset:
        while True:
            asks = client.rOrderBook(symbol,100,'asks')
            ask_price, asset_qty = mean_asks_price(coin_bal,asks)
            profit = asset_qty * (1 - taker) > coin_bal
            favorable_price = ask_price < last_price
            if profit and favorable_price:
                fix_qty = lot_size(asset_qty, step_size)
                response = client.marketBuy(symbol, fix_qty)
                lastprice = ask_price
                return response, last_price
            sleep(1)
    elif selling_asset:
        while True:
            bids = client.rOrderBook(symbol,100,'bids')
            bid_price, coin_qty = mean_bids_price(asset_bal,bids)
            profit = coin_qty * (1 - taker) > asset_bal
            favorable_price = bid_price > last_price
            if profit and favorable_price:
                fix_qty = lot_size(asset_bal, step_size)
                response = client.marketSell(symbol, fix_qty)
                lastprice = bid_price
                return response, last_price
            sleep(1)

def save_trade_history(response, last_price):
    if response is not None:
        data = open('trade_history.txt','a+')
        data.write(f'{response}\n')
        print(f"last price = {last_price:.5f}")

def main():
    client = binance(keys.binance_apikey, keys.binance_secret)
    coin = 'USDT'
    asset = 'TUSD'
    last_price = 1
    while True:
        try:
            response, last_price = automated_trade(coin,asset,client,last_price)
            save_trade_history(response,last_price)
        except KeyboardInterrupt:
            print('\nSTOPED BY USER')
            break
        except Exception as e:
            print(str(e))

if __name__ == '__main__':
    main()
