from time import sleep, ctime
from binance_api import binance
from math import floor
from decimal import Decimal
import keys

def start_msg():
    print(f"{' bot_stablecoin_binance ':-^35}")
    print(f"|{ctime():^33}|")

def monitor(func):
    def balances(coins, balance):
        balances_dict = func(coins, balance)
        print(f"{' Wallet balnces ':-^35}")
        for coin, balance in balances_dict.items():
            msg = f'{coin:<4}: {balance:>.8f}'
            print(f"|{msg:^33}|")
        return balances_dict
    return balances

@monitor
def get_balance(coins, all_balances):
    coin_balances = dict()
    for balance in all_balances:
        if balance['asset'] in coins:
            coin_balances[balance['asset']] = float(balance['free'])
    return coin_balances

def create_symbol(coin, asset):
    return f'{asset}{coin}'

def find_markets(coins, client):
    my_markets = []
    hypthetical_symbols = [create_symbol(coin,asset) for coin in coins for asset in coins]
    all_markets = client.eInfo()['symbols']
    for market in all_markets:
        real_symbol = market['symbol'] in hypthetical_symbols
        if real_symbol:
            my_markets.append(market['symbol'])
    return tuple(my_markets)

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

def lot_size(asset_qty, step_size=0.01):
    d = abs(Decimal(str(step_size)).as_tuple().exponent)
    fix_size = asset_qty % step_size
    return truncate(asset_qty - fix_size, d)

def diagram(coin, symbol, inital_qty, final_qty):
    print(f"{' Arbitrage trade ':-^35}")
    type_str = f"{'>':->10}" if coin in symbol[3:] else f"{'<':-<10}"
    msg_0 = f"{coin:>4} {type_str} {symbol.replace(coin,''):<4}"
    msg_1 = f'Profit: {100 * final_qty / inital_qty - 100:.8f}%'
    msg_2 = ctime()
    for msg in (msg_0, msg_1, msg_2):
        print(f"|{msg:^33}|")


def automated_trade(coins, client):
    balances = get_balance(coins, client.rBalances())
    taker = client.rTaker()
    coin, balance_qty = max(balances.items())
    my_markets = find_markets(coins,client)
    while True:
        # make purchase or sale
        for symbol in my_markets:
            if coin in symbol[3:]:
                # buy asset
                asks = client.rOrderBook(symbol,100,'asks')
                ask_price, asset_qty = mean_asks_price(balance_qty,asks)
                profit = lot_size(asset_qty) * (1 - taker) > lot_size(balance_qty)
                if profit and ask_price < 1:
                    lot_qty = lot_size(asset_qty)
                    response = client.marketBuy(symbol,lot_qty)
                    diagram(coin,symbol,balance_qty,asset_qty * (1-taker))
                    return response
            elif coin in symbol[:4]:
                # sell asset
                bids = client.rOrderBook(symbol,100,'bids')
                bid_price, coin_qty = mean_bids_price(balance_qty,bids)
                profit = lot_size(coin_qty) * (1 - taker) > lot_size(balance_qty)
                if profit and bid_price > 1:
                    lot_qty = lot_size(balance_qty)
                    response = client.marketSell(symbol,lot_qty)
                    diagram(coin,symbol,balance_qty,coin_qty * (1-taker))
                    return response
            sleep(1)

def save_trade_history(response):
    if response != None:
        data = open('trade_history.txt','a+')
        data.write(f'{response}\n')

def main():
    client = binance(keys.binance_apikey, keys.binance_secret)
    coins = ('USDT','TUSD','PAX','USDC')
    start_msg()
    while True:
        try:
            response = automated_trade(coins,client)
            save_trade_history(response)
            break
        except KeyboardInterrupt:
            print('\nSTOPED BY USER')
            break
        except TimeoutError:
            print('Timeout')
        except Exception as e:
            print(str(e))
