import aiohttp
import asyncio
import time
import hmac, hashlib
from urllib.parse import urlencode

class binance:

    def __init__(self, APIkey, Secret):
        """
        Client.
        """
        self.APIkey = APIkey
        self.Secret = Secret

    async def response_status(self, response):
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

    async def request(self, type, url, params, headers={}):
        async with aiohttp.ClientSession() as session:
            if type == 'GET':
                resp = await session.get(url, params=params, headers=headers)
            elif type == 'POST':
                resp = await session.post(url, params=params, headers=headers)
            elif type == 'DELETE':
                resp = await session.delete(url, params=params, headers=headers)
            elif type == 'PUT':
                resp = await session.put(url, params=params, headers=headers)
            return await self.response_status(resp)

    def api_query(self,command, params={}, reqType=None, privateAPI=False, signed=False):

        urlAPI = 'https://api.binance.com/api'
        urlPublic = urlAPI + '/v1'
        urlPrivate = urlAPI + '/v3'
        list1 = ('/ping', '/time', '/exchangeInfo')
        timestamp = int(time.time()*1000)
        recvWindow = 5000
        if privateAPI == False:
            url = urlPublic + command
            ret = self.request('GET', url, params=params)
        elif privateAPI == True and signed == False:
            url = urlPrivate + command
            ret = self.request('GET', url, params=params)
        elif signed == True:
            url = urlPrivate + command
            params['timestamp'] = timestamp
            params['recvWindow'] = recvWindow
            query_string = urlencode(params)
            sign = hmac.new(self.Secret.encode('UTF-8'), query_string.encode('UTF-8'), hashlib.sha256)
            params['signature'] = sign.hexdigest()
            headers = {'X-MBX-APIKEY': self.APIkey}
            ret = self.request(reqType, url, params=params, headers=headers)
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(ret)


#1-PUBLIC API METHODS
    def ping(self):
        """
        Test connectivity to the Rest API.
        """
        return self.api_query('/ping')

    def serverTime(self):
        """
        Test connectivity to the Rest API and get the current server time.
        """
        return self.api_query('/time')['serverTime']

    def eInfo(self):
        """
        Current exchange trading rules and symbol information.
        """
        x = self.api_query('/exchangeInfo')
        return json.dumps(x, indent=1)

    def rPrice(self, currencyPair):
        """
        Latest price for a symbol or symbols.
        :currencyPair: The currency pair, e.q. 'LTCBTC'.
        """
        params = {'symbol': currencyPair}
        x = self.api_query('/ticker/price', params=params)
        return float(x['price'])

    def rAllPrices(self):
        """
        Latest price for all symbols.
        """
        return self.api_query('/ticker/allPrices')

    def rOrderBook(self, currencyPair, depth=5, field=None):
        """
        Returns the order book for a given market.
        :currencyPair: The currency pair, e.q. 'LTCBTC'.
        :depth (default = 5): weight limit.
        :field (optional): Information from a specific field, such as 'lastUpdatedId', 'bids', 'asks'.
        Caution: setting limit=0 can return a lot of data.
        """
        params = {
            'symbol': currencyPair,
            'limit': depth
        }
        x = self.api_query('/depth', params=params)
        if field is not None and field in x:
            x = x[field]
            if field == 'asks' or field == 'bids':
                for elem in x:
                    for c, num in enumerate(elem):
                        elem[c] = float(num)
            else:
                x = int(x)
        return x


#2-PRIVATE API METHODS
    def order(self, reqType, currencyPair=None, orderId=None, origClientOrderId=None, params={}):
        """
        Create order of any kind, i.e. buy, sell, cancel, status, and so on.
        :currencyPair: The currency pair, e.q. 'LTCBTC'.
        :orderId: a given order ID.
        :origClientOrderId:
        """
        if currencyPair is not None:
            params['symbol'] = currencyPair
        if orderId is not None:
            params['orderId'] = orderId
        if origClientOrderId is not None:
            params['origClientOrderId'] = origClientOrderId
        return self.api_query('/order',privateAPI=True,signed=True,reqType=reqType,params=params)


    #2.1-requests GET
    def bookTicker(self, currencyPair, field=None):
        params = {'symbol': currencyPair}
        x = self.api_query('/ticker/bookTicker', params=params, privateAPI=True)
        if field is not None:
            x = x[field]
            if field != 'symbol':
                x = float(x)
        return x

    def aInfo(self, field=None):
        """
        Get current account information.
        :field (optional): 'balances', 'makerCommission', 'takerCommission', 'buyerCommission', 'sellerCommission', 'canTrade', 'canWithdraw', 'canDeposit', 'updateTime', and 'accountType'.
        """
        x = self.api_query('/account', params={}, privateAPI=True, signed=True, reqType='GET')
        if field is not None and x is not None:
            x = x[field]
        return x

    def rBalances(self, asset=None, status='free'):
        """
        Returns all of your balances.
        :asset (optional): A given currency.
        :status (default=free): 'asset' confirms our currency, 'free' and 'locked' amount of the given asset.
        """
        x = self.aInfo('balances')
        if asset is not None and x is not None:
            for c, k in enumerate(x):
                if k['asset'] == asset and status in {'free', 'locked'}:
                    balance = float(x[c][status])
                elif k['asset'] == asset:
                    balance = x[c][status]
        else:
            balance = x
        return balance

    def orderStatus(self, currencyPair, orderId, origClientOrderId):
        """
        Check an order's status.
        NOTE: check 'order' method in help.
        """
        return self.order(currencyPair,'GET', orderId=orderId, origClientOrderId=origClientOrderId)

    def openOrders(self,currencyPair=None):
        params = {}
        if currencyPair is not None:
            params['symbol'] = currencyPair
        return self.api_query('/openOrders',privateAPI=True,signed=True,reqType='GET',params=params)

    def allOrders(self, currencyPair, orderId=None, start=None, end=None):
        """
        Get all account orders; active, canceled, or filled.
        :currencyPair: The currency pair, e.q. 'LTCBTC'.
        :orderId (optional): a given order ID.
        :start (optional): start time.
        :end (optional): end time.
        """
        params = {'symbol':currencyPair}
        if orderId is not None:
            params['orderId'] = orderId
        if start is not None:
            params['startTime'] = start
        if end is not None:
            params['endTime'] = end
        return self.api_query('/allOrders',privateAPI=True,signed=True,reqType='GET',params=params)

    def myTrades(self, currencyPair, start=None, end=None,):
        """
        Get trades for a specific account and symbol.
        :currencyPair: The currency pair, e.q. 'LTCBTC'.
        :start (optional): start time.
        :end (optional): end time.
        """
        params = {'symbol':currencyPair}
        if startT is not None:
            params['startTime'] = start
        if endT is not None:
            params['endTime'] = end
        return self.api_query('/myTrades',privateAPI=True,signed=True,reqType='GET',params=params)


    #2.2-requests POST
    def testOrder(self, currencyPair, side, type, quantity, timeInForce=None, price=None, stopPrice=None, icebergQty=None, newOrderRespType=None):
        """
        Test new order creation and signature/recvWindow long. Creates and validates a new order but does not send it into the matching engine.
        :currencyPair: The currency pair, e.q. 'LTCBTC'.
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
            'symbol': currencyPair,
            'side' : side,
            'type' : type,
            'quantity' : str(quantity),
        }
        if timeInForce is not None:
            params['timeInForce'] = timeInForce
        if price is not None:
            params['price'] = str(price)
        if stopPrice is not None:
            params['stopPrice'] = str(stopPrice)
        if icebergQty is not None:
            params['icebergQty'] = str(icebergQty)
        if newOrderRespType is not None:
            params['newOrderRespType'] = newOrderRespType
        return self.api_query('/order/test',privateAPI=True,signed=True,reqType='POST',params=params)

    def newOrder(self, currencyPair, side, type, quantity, timeInForce=None, price=None, stopPrice=None, icebergQty=None, newOrderRespType=None):
        """
        Send in a new order.
        :currencyPair: The currency pair, e.q. 'LTCBTC'.
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
            'symbol': currencyPair,
            'side' : side,
            'type' : type,
            'quantity' : str(quantity),
        }
        if timeInForce is not None:
            params['timeInForce'] = timeInForce
        if price is not None:
            params['price'] = str(price)
        if stopPrice is not None:
            params['stopPrice'] = str(stopPrice)
        if icebergQty is not None:
            params['icebergQty'] = str(icebergQty)
        if newOrderRespType is not None:
            params['newOrderRespType'] = newOrderRespType
        return self.order('POST',params=params)


    #2.2.1-MARKET ORDERS
    def marketBuy(self, currencyPair, quantity):
        """
        Send a new MARKET order to buy.
        :currencyPair:
        :quantity:
        NOTE: check 'newOrder' method in help.
        """
        return self.newOrder(currencyPair,'BUY','MARKET', quantity)

    def marketSell(self, currencyPair, quantity):
        """
        Send a new MARKET order to sell.
        :currencyPair:
        :quantity:
        NOTE: check 'newOrder' method in help.
        """
        return self.newOrder(currencyPair,'SELL','MARKET', quantity)

    def stopLossBuy(self, currencyPair, quantity, stopPrice):
        """
        Send a new STOP_LOSS order to buy.
        :currencyPair:
        :quantity:
        :stopPrice:
        NOTE: check 'newOrder' method in help.
        """
        return self.newOrder(currencyPair,'BUY','STOP_LOSS',quantity,stopPrice)

    def stopLossSell(self, currencyPair, quantity, stopPrice):
        """
        Send a new STOP_LOSS order to sell.
        :currencyPair:
        :quantity:
        :stopPrice:
        NOTE: check 'newOrder' method in help.
        """
        return self.newOrder(currencyPair,'SELL','STOP_LOSS',quantity,stopPrice)


    #2.3-requests DELETE
    def cancelOrder(self, currencyPair, orderId, origClientOrderId):
        """
        Cancel an active order.
        NOTE: check 'order' method in help.
        """
        return self.order(currencyPair, orderId, origClientOrderId, reqType='DELETE')


    #2.4-requests PUT


#3-WEBSOCKETS API METHODS
