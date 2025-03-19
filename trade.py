import time
from binance import AsyncClient, BinanceSocketManager
import asyncio
from decimal import Decimal
from telebot.async_telebot import AsyncTeleBot

class Trade:
    def __init__(self):
        self.prices = {}
        self.orders = {}
        self.stop = {}
        self.streams = ["btctusd@trade", "btctusd@bookTicker"]
        self.secret = ""
        self.public = ""
        self.channel = ""
        self.telegram_bot_token = ''
        self.bot = AsyncTeleBot(self.telegram_bot_token)
        self.stop_procent = 0.15/100
        self.orderstime = {}
        self.buy_price = {}

    async def get_buy(self, pair):
        return self.buy_price[pair]

    async def sendmsg(self, msg):
        await self.bot.send_message(self.channel, msg, parse_mode="html")
    
    async def buy(self, pair):
        pair = str(pair).upper()
        if pair not in self.orders or self.orders[pair] == "0":
            client = await AsyncClient.create(api_key=self.public, api_secret=self.secret)
            # await client.get_open_orders(symbol=pair)
            # print('jtthjkthjk')
                                                
            def roundd(zxc, quantity):
                precision = Decimal(str(zxc)).as_tuple().exponent*(-1)
                number_str = str(quantity)
                result_str = number_str[:number_str.index('.') + precision + 1]
                return float(result_str)

            
            symbol_info = await client.get_symbol_info(symbol=pair)
            price = float(self.prices[pair]['a']) - float(symbol_info['filters'][0]['tickSize'])
            quantity = await client.get_asset_balance(symbol_info['quoteAsset'])
            print(quantity)

            amount = float(quantity['free']) / float(self.prices[pair]['a'])
            zxc= float(symbol_info['filters'][1]['stepSize'])
            price_filter= float(symbol_info['filters'][0]['minPrice'])
            price = roundd(zxc=price_filter, quantity=price)
            quantity = roundd(zxc=zxc, quantity=amount)
            # 'baseAsset' - base symb
            # 'quoteAsset' - quote symb
            # 'filters'[0]'tickSize' - знаков после точки в цене + минимальное изм цены

            await client.create_order(
                symbol=str(pair).upper(),
                side='BUY',
                type='LIMIT',
                quantity=quantity,
                price=price,
                timeInForce='GTC'
            )
            self.orders[pair] = "1"
            await client.close_connection()

    async def sell(self, pair):
        pair = str(pair).upper()
        # if pair in self.orders and self.orders[pair] == "1":
        if 1 == 1:
            client = await AsyncClient.create(api_key=self.public, api_secret=self.secret)
            orders = await client.get_open_orders(symbol=pair)
            for i in orders:
                if i != None:
                    if i['symbol'] == pair:
                        order_id = i['orderId']
                        await client.cancel_order(symbol=pair, orderId=order_id)
            # await asyncio.sleep(1)
            async def roundd(zxc, quantity):
                precision = Decimal(str(zxc)).as_tuple().exponent*(-1)
                number_str = str(quantity)
                result_str = number_str[:number_str.index('.') + precision + 1]
                return float(result_str)
            symbol_info = await client.get_symbol_info(symbol=pair)
            price = float(self.prices[pair]['b']) + float(symbol_info['filters'][0]['tickSize'])
            quantity = await client.get_asset_balance(symbol_info['baseAsset'])
            zxc= float(symbol_info['filters'][1]['stepSize'])
            price_filter= float(symbol_info['filters'][0]['minPrice'])
            price = await roundd(price_filter, price)
            quantity = await roundd(zxc, quantity['free'])
            # precision = Decimal(str(zxc)).as_tuple().exponent*(-1)
            # quantity = int(float(precision) * 10 ** precision) / 10 ** precision
            
            await client.create_order(
                symbol=str(pair).upper(),
                side='SELL',
                type='LIMIT',
                quantity=quantity,
                price=price,
                timeInForce='GTC'
            )
            self.orders[pair] = "0"
            await client.close_connection()

    async def create_stop(self, pair, price, amount):
        def roundd(zxc, quantity):
            precision = Decimal(str(zxc)).as_tuple().exponent*(-1)
            number_str = str(quantity)
            result_str = number_str[:number_str.index('.') + precision + 1]
            return float(result_str)
        client = await AsyncClient.create(api_key=self.public, api_secret=self.secret)
        price_stop = float(price) - float(price) * self.stop_procent
        symbol_info = await client.get_symbol_info(symbol=pair)
        zxc= symbol_info['filters'][0]['minPrice']
        lfilter = symbol_info['filters'][1]['stepSize']
        price = roundd(zxc=float(zxc), quantity=price_stop)
        quantity = roundd(zxc=lfilter, quantity=amount)
        await client.create_order(
            symbol=str(pair).upper(),
            side='SELL',
            type='STOP_LOSS_LIMIT',
            quantity=quantity,
            price=price,
            timeInForce='GTC',
            stopPrice = price
        )
        await client.close_connection()
        
    async def create_stop_global(self, pair, price, amount):
        def roundd(zxc, quantity):
            precision = Decimal(str(zxc)).as_tuple().exponent*(-1)
            number_str = str(quantity)
            result_str = number_str[:number_str.index('.') + precision + 1]
            return float(result_str)
        client = await AsyncClient.create(api_key=self.public, api_secret=self.secret)
        price_stop = float(price)
        symbol_info = await client.get_symbol_info(symbol=pair)
        zxc= symbol_info['filters'][0]['minPrice']
        lfilter = symbol_info['filters'][1]['stepSize']
        price = roundd(zxc=float(zxc), quantity=price_stop)
        quantity = roundd(zxc=lfilter, quantity=amount)
        await client.create_order(
            symbol=str(pair).upper(),
            side='SELL',
            type='STOP_LOSS_LIMIT',
            quantity=quantity,
            price=price,
            timeInForce='GTC',
            stopPrice = price
        )
        await client.close_connection()
    
    async def timer(self):
        while True:
            for i in self.orderstime:
                if self.orderstime[i]['status'] == True:
                    if time.time() - self.orderstime[i]['time'] > 15:
                        print(self.orderstime[i]['side'])
                        self.orderstime[i]['status'] = False  
                        await self.reorder(pair=i, side=self.orderstime[i]['side'])
            await asyncio.sleep(1)

    async def reorder(self, pair, side):
        client = await AsyncClient.create(api_key=self.public, api_secret=self.secret)
        # if self.orderstime[pair]['status'] == True:
        if side == "SELL":
            await self.sell(pair)
            self.orderstime[pair]['status'] = False
            await client.close_connection()
        if side == "BUY":
            orders = await client.get_open_orders(symbol=pair)
            for i in orders:
                if i != None:
                    if i['symbol'] == pair:
                        order_id = i['orderId']
                        await client.cancel_order(symbol=pair, orderId=order_id)
                        self.orders[pair] = '0'
                        self.orderstime[pair]['status'] = False  
                        await self.buy(pair)
                        await client.close_connection()

    async def price(self):
        client = await AsyncClient.create(api_key=self.public, api_secret=self.secret)
        bm = BinanceSocketManager(client)
        ms = bm.multiplex_socket(self.streams)
        async with ms as tscm:
            while True:
                res = await tscm.recv()
                await self.on_message(res, who="public", client=client)

    async def sub(self):
        client = await AsyncClient.create(api_key=self.public, api_secret=self.secret)
        bm = BinanceSocketManager(client)
        us = bm.user_socket()
        async with us as tscm:
            while True:
                res = await tscm.recv()
                print(res)
                await self.on_message(res, who="private", client=client)

    async def on_message(self, msg, who):
        # print(msg, who)
        if who == "public":
            pair = msg['data']['s']
            if pair in self.prices:
                if "trade" in msg['stream']:
                    self.prices[pair]['p'] = msg['data']['p']
                elif "book" in msg['stream']:
                    self.prices[pair]['b'] = msg['data']['b']
                    self.prices[pair]['a'] = msg['data']['a']
                else:
                    print(msg)
            else:
                self.prices[pair] = {}

        elif who == "private":
            # print(msg)
            if msg['e'] == 'executionReport':
                if msg['S'] == 'SELL':
                    if msg['X'] == 'FILLED':
                        client = await AsyncClient.create(api_key=self.public, api_secret=self.secret)
                        if msg['o'] == 'STOP_LOSS_LIMIT':
                            bal = await client.get_asset_balance("TUSD")
                            await self.sendmsg(f"Пара: {pair} \nКол-во {bal} \nТип: STOP")
                            self.orders[pair] = "0"
                        if msg['o'] == 'LIMIT':
                            bal = await client.get_asset_balance("TUSD")
                            pair = msg['s']
                            await self.sendmsg(f"Пара: {pair} \nКол-во {bal} \nТип: {msg['S']}")
                            self.orderstime[pair] = {'status' : False, 'time': time.time(), 'side': "SELL"}
                    elif msg['X'] == 'NEW':
                        if msg['o'] == 'LIMIT':
                            pair = msg['s']
                            self.orderstime[pair] = {'status' : True, 'time': time.time(), 'side': "SELL"}

                if msg['S'] == 'BUY':
                    if msg['X'] == 'FILLED':
                        pair = msg['s']
                        await self.create_stop(pair=pair, price=msg['p'], amount=msg['q'])
                        await self.sendmsg(f"Пара: {pair}\n Кол-во {msg['q']} \nТип: {msg['S']}")
                        self.orderstime[pair] = {'status' : False, 'time': time.time(), 'side': "BUY"}
                        self.buy_price[pair] = float(msg['p'])
                    elif msg['X'] == 'NEW':
                        if msg['o'] == 'LIMIT':
                            pair = msg['s']
                            self.orderstime[pair] = {'status' : True, 'time': time.time(), 'side': "BUY"}
                



            # "c" - client order id (stop_loss)
            # "S" - Side (Telegram)
            # "q" - quantity (Telegram)
            # "p" - order price (Telegram)
            # "X" - Current order status (Telegram, stop_loss)
            # "r" - Order reject reason; will be an error code (debug inf)


trade = Trade()
async def main():
    await asyncio.sleep(5)
    try:
        await trade.sell(pair="btctusd")
    except Exception as e:
        print(e)
async def run():
    task = asyncio.create_task(trade.sub())
    task2 = asyncio.create_task(trade.price())
    task4 = asyncio.create_task(trade.timer())
    task3 = asyncio.create_task(main())
    await asyncio.gather(task, task2, task3, task4)
asyncio.run(run())
