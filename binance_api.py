import aiohttp
import asyncio
import time
import hmac, hashlib
from urllib.parse import urlencode

class binance:

    def __init__(self, APIkey=None, Secret=None):
        """
        Client.
        """
        self.APIkey = APIkey
        self.Secret = Secret

    def __repr__(self):
            signature = self.APIkey != None and self.Secret != None
            return "{}igned Binance API".format("S" if signature else "Uns")

    async def _response_status(self, response):
        if response.status == 200:
            return await response.json()
        elif response.status == 400:
            error = await response.json()
            print(f"Error{error['code']}: {error['msg']}")
        elif response.status == 443:
            print("Connection reset by peer")
        elif response.status == 504:
            print("Gateway Time-out")
        else:
            print(response.status)
            print(await response.text())

    async def _request(self, type, url, params, headers={}):
        async with aiohttp.ClientSession() as session:
            if type == 'GET':
                resp = await session.get(url, params=params, headers=headers)
            elif type == 'POST':
                resp = await session.post(url, params=params, headers=headers)
            elif type == 'DELETE':
                resp = await session.delete(url, params=params, headers=headers)
            elif type == 'PUT':
                resp = await session.put(url, params=params, headers=headers)
            return await self._response_status(resp)

    def _api_query(self,command, params={}, request_type=None, private_api=False, signed=False):

        url_api = 'https://api.binance.com/api'
        url_public = url_api + '/v1'
        url_private = url_api + '/v3'
        timestamp = int(time.time()*1000)
        recvWindow = 5000
        if private_api == False:
            url = url_public + command
            ret = self._request('GET', url, params=params)
        elif private_api == True and signed == False:
            url = url_private + command
            ret = self._request('GET', url, params=params)
        elif signed == True:
            url = url_private + command
            params['timestamp'] = timestamp
            params['recvWindow'] = recvWindow
            query_string = urlencode(params)
            sign = hmac.new(self.Secret.encode('UTF-8'), query_string.encode('UTF-8'), hashlib.sha256)
            params['signature'] = sign.hexdigest()
            headers = {'X-MBX-APIKEY': self.APIkey}
            ret = self._request(request_type, url, params=params, headers=headers)
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(ret)


#1-PUBLIC API METHODS
    def ping(self):
        """
        Test connectivity to the Rest API.
        """
        return self._api_query('/ping')

    def serverTime(self):
        """
        Test connectivity to the Rest API and get the current server time.
        """
        return self._api_query('/time')['serverTime']

    def eInfo(self):
        """
        Current exchange trading rules and symbol information.
        """
        return self._api_query('/exchangeInfo')

    def rPrice(self, currency_pair):
        """
        Latest price for a symbol or symbols.
        :currency_pair: The currency pair, e.q. 'LTCBTC'.
        """
        params = {'symbol': currency_pair}
        price = self._api_query('/ticker/price', params=params)
        return float(price['price'])

    def rAllPrices(self):
        """
        Latest price for all symbols.
        """
        return self._api_query('/ticker/allPrices')

    def rOrderBook(self, currency_pair, depth=100, field=None):
        """
        Returns the order book for a given market.
        :currency_pair: The currency pair, e.q. 'LTCBTC'.
        :depth (default = 5): weight limit.
        :field (optional): Information from a specific field, such as 'lastUpdatedId', 'bids', 'asks'.
        Caution: setting limit=0 can return a lot of data.
        """
        params = {
            'symbol': currency_pair,
            'limit': depth
        }
        order_book = self._api_query('/depth', params=params)
        for key, value in order_book.items():
            if key in ['asks','bids']:
                for elem in value:
                    for c, num in enumerate(elem):
                        elem[c] = float(num)
        if field != None and field in order_book:
            return order_book[field]
        else:
            return order_book


#2-PRIVATE API METHODS
    def _order(self, request_type, currency_pair=None, order_id=None, orig_client_order_id=None, params={}):
        """
        Create order of any kind, i.e. buy, sell, cancel, status, and so on.
        :currency_pair: The currency pair, e.q. 'LTCBTC'.
        :order_id: a given order ID.
        :orig_client_order_id:
        """
        if currency_pair != None:
            params['symbol'] = currency_pair
        if order_id != None:
            params['orderId'] = order_id
        if orig_client_order_id != None:
            params['origClientOrderId'] = orig_client_order_id
        return self._api_query('/order',private_api=True,signed=True,request_type=request_type,params=params)


    #2.1-requests GET
    def r24hTicker(self, currency_pair=None, field=None):
        params = {}
        if currency_pair != None:
            params = {'symbol' : currency_pair}
        r24h_ticker = self._api_query('/ticker/24hr', params = params, private_api=True)
        if field != None:
            r24h_ticker = r24h_ticker[field]
            if field not in ('symbol','openTime','closeTime','firstId','lastId','count'):
                r24h_ticker = float(r24h_ticker)
        return r24h_ticker

    def bookTicker(self, currency_pair=None, field=None):
        """
        Best price and quantity on the order book for a symbol or symbols.
        :currency_pair (optional): The symbol of a given market, e.q. 'LTCBTC'
        :field (optional): 'symbol', 'bidPrice', 'bidQty', 'askPrice', and 'askQty'.
        """
        params = {}
        if currency_pair != None:
            params = {'symbol': currency_pair}
        book_ticker = self._api_query('/ticker/bookTicker', params=params, private_api=True)
        if field != None:
            book_ticker = book_ticker[field]
            if field != 'symbol':
                book_ticker = float(book_ticker)
        return book_ticker

    def aInfo(self, field=None):
        """
        Get current account information.
        :field (optional): 'balances', 'makerCommission', 'takerCommission', 'buyerCommission', 'sellerCommission', 'canTrade', 'canWithdraw', 'canDeposit', 'updateTime', and 'accountType'.
        """
        info = self._api_query('/account', params={}, private_api=True, signed=True, request_type='GET')
        if field != None and info != None:
            info = info[field]
        return info

    def rBalances(self, asset=None, status='free'):
        """
        Returns all of your balances.
        :asset (optional): A given currency.
        :status (default=free): 'asset' confirms our currency, 'free' and 'locked' amount of the given asset.
        """
        balances = self.aInfo('balances')
        if asset != None and balances != None:
            for c, k in enumerate(balances):
                if k['asset'] == asset and status in {'free', 'locked'}:
                    balance = float(balances[c][status])
                elif k['asset'] == asset:
                    balance = balances[c][status]
        else:
            balance = balances
        return balance

    def rTaker(self):
        """
        Returns taker commission in percentage. For instance, if commission is of 0.1% the value exhibited is 0.001.
        """
        taker = self.aInfo('takerCommission') / 10000
        return taker

    def rMaker(self):
        """
        Returns maker commission in percentage. For instance, if commission is of 0.1% the value exhibited is 0.001.
        """
        maker = self.aInfo('takerCommission') / 10000
        return maker

    def orderStatus(self, currency_pair, order_id, orig_client_order_id):
        """
        Check an order's status.
        NOTE: check 'order' method in help.
        """
        return self._order(currency_pair,'GET', order_id=order_id, orig_client_order_id=orig_client_order_id)

    def openOrders(self,currency_pair=None):
        params = {}
        if currency_pair != None:
            params['symbol'] = currency_pair
        return self._api_query('/openOrders',private_api=True,signed=True,request_type='GET',params=params)

    def allOrders(self, currency_pair, order_id=None, start=None, end=None):
        """
        Get all account orders; active, canceled, or filled.
        :currency_pair: The currency pair, e.q. 'LTCBTC'.
        :order_id (optional): a given order ID.
        :start (optional): start time.
        :end (optional): end time.
        """
        params = {'symbol':currency_pair}
        if order_id != None:
            params['orderId'] = order_id
        if start != None:
            params['startTime'] = start
        if end != None:
            params['endTime'] = end
        return self._api_query('/allOrders',private_api=True,signed=True,request_type='GET',params=params)

    def myTrades(self, currency_pair, start=None, end=None,):
        """
        Get trades for a specific account and symbol.
        :currency_pair: The currency pair, e.q. 'LTCBTC'.
        :start (optional): start time.
        :end (optional): end time.
        """
        params = {'symbol':currency_pair}
        if start != None:
            params['startTime'] = start
        if end != None:
            params['endTime'] = end
        return self._api_query('/myTrades',private_api=True,signed=True,request_type='GET',params=params)


    #2.2-requests POST
    def testOrder(self, currency_pair, side, type, quantity, timeInForce=None, price=None, stopPrice=None, icebergQty=None, newOrderRespType=None):
        """
        Test new order creation and signature/recvWindow long. Creates and validates a new order but does not send it into the matching engine.
        :currency_pair: The currency pair, e.q. 'LTCBTC'.
        :side: BUY or SELL.
        :type: LIMIT, MARKET, STOP_LOSS, STOP_LOSS_LIMIT, TAKE_PROFIT, TAKE_PROFIT_LIMIT, LIMIT_MAKER.
        :quantity (decimal value): Quantity of the given asset.
        :price (decimal value): Price of the given asset.
        :stopPrice (decimal value): Used with STOP_LOSS, STOP_LOSS_LIMIT, TAKE_PROFIT, and TAKE_PROFIT_LIMIT orders.
        :timeInForce: GTC (good till canceled), IOC (immediate or cancel), or FOK (fill or kill).
        :icebergQty (decimal value): Used with LIMIT, STOP_LOSS_LIMIT, and TAKE_PROFIT_LIMIT to create an iceberg order.
        :newOrderRespType: Set the response JSON. ACK, RESULT, or FULL; MARKET and LIMIT order types default to FULL, all other orders default to ACK.
        """
        params = {
            'symbol': currency_pair,
            'side' : side,
            'type' : type,
            'quantity' : str(quantity),
        }
        if timeInForce != None:
            params['timeInForce'] = timeInForce
        if price != None:
            params['price'] = str(price)
        if stopPrice != None:
            params['stopPrice'] = str(stopPrice)
        if icebergQty != None:
            params['icebergQty'] = str(icebergQty)
        if newOrderRespType != None:
            params['newOrderRespType'] = newOrderRespType
        return self._api_query('/order/test',private_api=True,signed=True,request_type='POST',params=params)

    def newOrder(self, currency_pair, side, type, quantity, timeInForce=None, price=None, stopPrice=None, icebergQty=None, newOrderRespType=None):
        """
        Send in a new order.
        :currency_pair: The currency pair, e.q. 'LTCBTC'.
        :side: BUY or SELL.
        :type: LIMIT, MARKET, STOP_LOSS, STOP_LOSS_LIMIT, TAKE_PROFIT, TAKE_PROFIT_LIMIT, LIMIT_MAKER.
        :quantity (decimal value): Quantity of the given asset.
        :price (decimal value): Price of the given asset.
        :stopPrice (decimal value): Used with STOP_LOSS, STOP_LOSS_LIMIT, TAKE_PROFIT, and TAKE_PROFIT_LIMIT orders.
        :timeInForce: GTC (good till canceled), IOC (immediate or cancel), or FOK (fill or kill).
        :icebergQty (decimal value): Used with LIMIT, STOP_LOSS_LIMIT, and TAKE_PROFIT_LIMIT to create an iceberg order.
        :newOrderRespType: Set the response JSON. ACK, RESULT, or FULL; MARKET and LIMIT order types default to FULL, all other orders default to ACK.

        TYPE                | MANDATORY PARAMETERS:
        - LIMIT             | timeInForce, quantity, price
        - MAKET             | quantity
        - STOP_LOSS         | quantity, stopPrice
        - STOP_LOSS_LIMIT   | timeInForce, quantity, price, stopPrice
        - TAKE_PROFIT       | quantity, stopPrice
        - TAKE_PROFIT_LIMIT | timeInForce, quantity, price, stopPrice
        - LIMIT_MAKER       | quantity, price

        OTHER INFO:
        - LIMIT_MAKER are LIMIT orders that will be rejected if they would immediately match and trade as a taker.
        - STOP_LOSS and TAKE_PROFIT will execute a MARKET order when the stopPrice is reached.
        - Any LIMIT or LIMIT_MAKER type order can be made an iceberg order by sending an icebergQty.
        - Any order with an icebergQty MUST have timeInForce set to GTC.

        Trigger order price rules against market price for both MARKET and LIMIT versions:
        - Price above market price: STOP_LOSS BUY, TAKE_PROFIT SELL
        - Price below market price: STOP_LOSS SELL, TAKE_PROFIT BUY

        NOTE: check 'order' method in help.
        """
        params = {
            'symbol': currency_pair,
            'side' : side,
            'type' : type,
            'quantity' : str(quantity),
        }
        if timeInForce != None:
            params['timeInForce'] = timeInForce
        if price != None:
            params['price'] = str(price)
        if stopPrice != None:
            params['stopPrice'] = str(stopPrice)
        if icebergQty != None:
            params['icebergQty'] = str(icebergQty)
        if newOrderRespType != None:
            params['newOrderRespType'] = newOrderRespType
        return self._order('POST',params=params)


    #2.2.1-MARKET ORDERS
    def marketBuy(self, currency_pair, quantity):
        """
        Send a new MARKET order to buy.
        :currency_pair:
        :quantity:
        NOTE: check 'newOrder' method in help.
        """
        return self.newOrder(currency_pair=currency_pair,
                             side='BUY',
                             type='MARKET',
                             quantity=quantity)

    def marketSell(self, currency_pair, quantity):
        """
        Send a new MARKET order to sell.
        :currency_pair:
        :quantity:
        NOTE: check 'newOrder' method in help.
        """
        return self.newOrder(currency_pair=currency_pair,
                             side='SELL',
                             type='MARKET',
                             quantity=quantity)

    def stopLossBuy(self, currency_pair, quantity, stopPrice):
        """
        Send a new STOP_LOSS order to buy.
        :currency_pair:
        :quantity:
        :stopPrice:
        NOTE: check 'newOrder' method in help.
        """
        return self.newOrder(currency_pair=currency_pair,
                             side='BUY',
                             type='STOP_LOSS',
                             quantity=quantity,
                             stopPrice=stopPrice)

    def stopLossSell(self, currency_pair, quantity, stopPrice):
        """
        Send a new STOP_LOSS order to sell.
        :currency_pair:
        :quantity:
        :stopPrice:
        NOTE: check 'newOrder' method in help.
        """
        return self.newOrder(currency_pair=currency_pair,
                        side='SELL',
                        type='STOP_LOSS',
                        quantity=quantity,
                        stopPrice=stopPrice)


    #2.3-requests DELETE
    def cancelOrder(self, currency_pair, order_id, orig_client_order_id):
        """
        Cancel an active order.
        NOTE: check 'order' method in help.
        """
        return self._order(request_type='DELETE',
                           currency_pair=currency_pair,
                           order_id=order_id,
                           orig_client_order_id=orig_client_order_id)


    #2.4-requests PUT


#3-WEBSOCKETS API METHODS
