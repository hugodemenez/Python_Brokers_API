r"""
Python functions for crypto-brokers API
"""

__author__ = 'Hugo Demenez <hdemenez@hotmail.fr>'

import time,hmac,hashlib,requests,math,re
from urllib.parse import urljoin, urlencode


class binance:
    '''API development for trade automation in binance markets'''
    def __init__(self):
        self.API_SECRET=''
        self.API_KEY=''

    def truncate(self,number, digits) -> float:
        stepper = 10.0 ** digits
        return math.trunc(stepper * number) / stepper

    def symbol_format(self,symbol):
        return re.sub("[^0-9a-zA-Z]+", "", symbol)

    def create_key_file(self): 
        """Function to create your .key file"""
        API_KEY = str(input("Enter your API key :"))
        SECRET_KEY = str(input("Enter your SECRET_KEY :"))
        file = open("binance.key","w")
        file.write(API_KEY+'\n')
        file.write(SECRET_KEY)
        file.close()
        return True

    def get_server_time(self):
        '''Function to get server time'''
        response = requests.get('https://api.binance.com/api/v3/time',params={}).json()
        try:
            return response['serverTime']
        except:
            return('unable to get server time')
     
    def get_24h_stats(self,symbol):
        symbol = self.symbol_format(symbol)
        '''Function to get statistics for the last 24h'''
        response = requests.get('https://api.binance.com/api/v3/ticker/24hr',params={'symbol':symbol}).json()
        try:
            stats={
                'volume':response['volume'],
                'open':response['openPrice'],
                'high':response['highPrice'],
                'low':response['lowPrice'],
                'last':response['lastPrice'],
            }
        except:
            stats={
                'error':response,
            }
        finally:
            return stats
       
    def get_klines_data(self,symbol,interval):
        symbol = self.symbol_format(symbol)
        """Function to get information from candles of 1minute interval
        <time>, <open>, <high>, <low>, <close>, <volume>
        since (1hour for minutes or 1week for days)
        max timeframe is 12hours for minute interval 
        max timeframe is 30 days for hour interval
        max timeframe is 100 weeks for day interval
        """
        if interval=='day':
            interval='1d'
        elif interval=='hour':
            interval='1h'
        elif interval=='minute':
            interval='1m'
        else:
            return ('wrong interval')

        response = requests.get('https://api.binance.com/api/v3/klines',params={'symbol':symbol,'interval':interval,'limit':720}).json()
        try :
            formated_response=[]
            for info in response:
                data={}
                data['time']=int(round(info[0]/1000,0))
                data['open']=float(info[1])
                data['high']=float(info[2])
                data['low']=float(info[3])
                data['close']=float(info[4])
                data['volume']=float(info[5])

                formated_response.append(data)
        except:
            formated_response = 'error'
        return formated_response

 
    def connect_key(self,path):
        '''Function to connect the api to the account'''
        try:
            with open(path, 'r') as f:
                self.API_KEY = f.readline().strip()
                self.API_SECRET = f.readline().strip()
            return ("Successfuly connected your keys")
        except:
            return ("Unable to read .key file")
        
    def price(self,symbol):
        symbol = self.symbol_format(symbol)
        '''Function to get symbol prices'''
        response = requests.get('https://api.binance.com/api/v3/ticker/bookTicker',params={'symbol':symbol}).json()
        try:
            bid=float(response['bidPrice'])
            ask=float(response['askPrice'])
            price={'bid':bid,'ask':ask}
        except:
            return response['msg']
        return price

    def account_information(self):
        '''Function to get account information'''
        timestamp = self.get_server_time()
        recvWindow=10000
        params = {
            'timestamp': timestamp,
            'recvWindow':recvWindow,
        }
        query_string = urlencode(params)
        params['signature'] = hmac.new(self.API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        headers = {'X-MBX-APIKEY': self.API_KEY}
        url = urljoin('https://api.binance.com','/api/v3/account')
        response = requests.get(url, headers=headers, params=params).json()
        return response

    def get_balances(self,asset):
        '''Function to get account balances'''
        try:
            balances=self.account_information()['balances']
            for balance in balances:
                if balance['asset']==asset:
                    return balance
        except:
            return {'error':'unable to get balances'}

    def get_open_orders(self):
        '''Function to get open orders'''
        timestamp = self.get_server_time()
        params = {
            'timestamp': timestamp,
        }
        query_string = urlencode(params)
        params['signature'] = hmac.new(self.API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        headers = {'X-MBX-APIKEY': self.API_KEY}
        url = urljoin('https://api.binance.com','/api/v3/openOrders')
        response = requests.get(url, headers=headers, params=params).json()
        try:
            code = response['code']
            return ('Unable to get orders')
        except:
            if response==[]:
                return {}
        finally:
            return response

    def create_limit_order(self,symbol,side,price,quantity):
        symbol = self.symbol_format(symbol)
        '''Function to create a limit order'''
        timestamp = self.get_server_time()
        recvWindow=10000
        params = {
            'symbol':symbol,
            'side':side,
            'type':'LIMIT',
            'timeInForce':'GTC',
            'quantity':self.truncate(quantity,self.get_quantity_precision(symbol)),
            'price':self.truncate(price,self.get_price_precision(symbol)),
            'timestamp': timestamp,
            'recvWindow':recvWindow,
        }
        query_string = urlencode(params)
        params['signature'] = hmac.new(self.API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        headers = {'X-MBX-APIKEY': self.API_KEY}
        url = urljoin('https://api.binance.com','/api/v3/order')
        response = requests.post(url, headers=headers, params=params).json()
        return response

    def create_market_order(self,symbol,side,quantity):
        symbol = self.symbol_format(symbol)
        '''Function to create market order
        quantity = quantity to spend if it is buy in EUR
        '''
        timestamp = self.get_server_time()
        recvWindow=10000
        if side == 'buy':
            params = {
                'symbol':symbol,
                'side':side,
                'type':'MARKET',
                'quoteOrderQty':self.truncate(quantity,self.get_quantity_precision(symbol)),
                'timestamp': timestamp,
                'recvWindow':recvWindow,
            }
        elif side=='sell':
            params = {
                'symbol':symbol,
                'side':side,
                'type':'MARKET',
                'quantity':self.truncate(quantity,self.get_quantity_precision(symbol)),
                'timestamp': timestamp,
                'recvWindow':recvWindow,
            }
        query_string = urlencode(params)
        params['signature'] = hmac.new(self.API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        headers = {'X-MBX-APIKEY': self.API_KEY}
        url = urljoin('https://api.binance.com','/api/v3/order')
        response = requests.post(url, headers=headers, params=params).json()
        return response

    def create_stop_loss_order(self,symbol,quantity,stopPrice):
        symbol = self.symbol_format(symbol)
        '''Function to create a stop loss'''
        timestamp = self.get_server_time()
        recvWindow=10000
        params = {
            'symbol':symbol,
            'side':'sell',
            'type':'STOP_LOSS_LIMIT',
            'timeInForce':'GTC',
            'quantity':self.truncate(quantity,self.get_quantity_precision(symbol)),
            'stopPrice':self.truncate(stopPrice,self.get_price_precision(symbol)),
            'price':self.truncate(stopPrice*0.999,self.get_price_precision(symbol)),
            'timestamp': timestamp,
            'recvWindow':recvWindow,
        }
        query_string = urlencode(params)
        params['signature'] = hmac.new(self.API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        headers = {'X-MBX-APIKEY': self.API_KEY}
        url = urljoin('https://api.binance.com','/api/v3/order')
        response = requests.post(url, headers=headers, params=params).json()
        return response

    def create_take_profit_order(self,symbol,quantity,profitPrice):
        symbol = self.symbol_format(symbol)
        '''Function to create a take profit order (limit sell)'''
        timestamp = self.get_server_time()
        recvWindow=10000
        params = {
            'symbol':symbol,
            'side':'sell',
            'type':'LIMIT',
            'timeInForce':'GTC',
            'quantity':self.truncate(quantity,self.get_quantity_precision(symbol)),
            'price':self.truncate(profitPrice,self.get_price_precision(symbol)),
            'timestamp': timestamp,
            'recvWindow':recvWindow,
        }
        query_string = urlencode(params)
        params['signature'] = hmac.new(self.API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        headers = {'X-MBX-APIKEY': self.API_KEY}
        url = urljoin('https://api.binance.com','/api/v3/order')
        response = requests.post(url, headers=headers, params=params).json()
        try :
            response['msg']
            return response
        except:
            return response


    def query_order(self,symbol,orderid):
        symbol = self.symbol_format(symbol)
        '''Function to query order data'''
        timestamp = self.get_server_time()
        recvWindow=10000
        params = {
            'symbol':symbol,
            'orderId':orderid,
            'timestamp': timestamp,
            'recvWindow':recvWindow,
        }
        query_string = urlencode(params)
        params['signature'] = hmac.new(self.API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        headers = {'X-MBX-APIKEY': self.API_KEY}
        url = urljoin('https://api.binance.com','/api/v3/order')
        response = requests.post(url, headers=headers, params=params).json()
        return response
        
    def test_order(self):
        '''Function to create market order'''
        timestamp = self.get_server_time()
        recvWindow=10000
        params = {
            'symbol':'BTCEUR',
            'side':'buy',
            'type':'MARKET',
            'quantity':1,
            'timestamp': timestamp,
            'recvWindow':recvWindow,
        }
        query_string = urlencode(params)
        params['signature'] = hmac.new(self.API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        headers = {'X-MBX-APIKEY': self.API_KEY}
        url = urljoin('https://api.binance.com','/api/v3/order/test')
        response = requests.post(url, headers=headers, params=params).json()
        try:
            response['msg']
            return False
        except:
            return True

    def cancel_all_orders(self,symbol):
        symbol = self.symbol_format(symbol)
        '''Function to query order data'''
        timestamp = self.get_server_time()
        recvWindow=10000
        params = {
            'symbol':symbol,
            'timestamp': timestamp,
            'recvWindow':recvWindow,
        }
        query_string = urlencode(params)
        params['signature'] = hmac.new(self.API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        headers = {'X-MBX-APIKEY': self.API_KEY}
        url = urljoin('https://api.binance.com','/api/v3/openOrders')
        response = requests.delete(url, headers=headers, params=params).json()
        try:
            response['msg']
            return response
        except:
            return response
        
    def get_price_precision(self,symbol):
        symbol = self.symbol_format(symbol)
        while(True):
            try:
                info = self.get_exchange_info()
                for pair in info['symbols']:
                    if pair['symbol']==symbol:
                        precision = (len(str(pair['filters'][0]['minPrice']).rstrip('0').rstrip('.').replace('.','')))
                        return precision-1
                return {'error':'No matching symbol'}
            except:
                pass

    def get_quantity_precision(self,symbol):
        symbol = self.symbol_format(symbol)
        while(True):
            try:
                info = self.get_exchange_info()
                for pair in info['symbols']:
                    if pair['symbol']==symbol:
                        precision = (len(str(pair['filters'][2]['minQty']).rstrip('0').rstrip('.').replace('.','')))
                        return precision-1
                return {'error':'No matching symbol'}
            except:
                pass


    def get_exchange_info(self):
        '''Function to get open orders'''
        url = urljoin('https://api.binance.com','/api/v3/exchangeInfo')
        response = requests.get(url).json()
        try:
            response['code']
            return ('Unable to get info')
        except:
            if response==[]:
                return {}
        finally:
            return response
        
    def get_filters(self,symbol):
        symbol = self.symbol_format(symbol)
        while(True):
            try :
                info = self.get_exchange_info()
                filters={}
                for pair in info['symbols']:
                    if pair['symbol']==symbol:
                        for filter in pair['filters']:
                            filters[filter['filterType']]=filter
                        return filters
            except:
                pass


class ftx:
    def __init__(self):
        self.API_SECRET=''
        self.API_KEY=''
        self.ENDPOINT='https://ftx.com/api'

    def symbol_format(self,symbol):
        return re.sub("[^0-9a-zA-Z]+", "/", symbol)

    def connect_key(self,path):
        '''Function to connect the api to the account'''
        try:
            with open(path, 'r') as f:
                self.API_KEY = f.readline().strip()
                self.API_SECRET = f.readline().strip()
            return ("Successfuly connected your keys")
        except:
            return ("Unable to read .key file")

    def create_key_file(self): 
        """Function to create your .key file"""
        API_KEY = str(input("Enter your API key :"))
        SECRET_KEY = str(input("Enter your SECRET_KEY :"))
        file = open("ftx.key","w")
        file.write(API_KEY+'\n')
        file.write(SECRET_KEY)
        file.close()
        return True



    def get_exchange_info(self):
        '''Function to get server time'''
        response = requests.get(self.ENDPOINT+'/markets',params={}).json()
        try:
            return response
        except:
            return('unable to get server time')


    def get_price_precision(self,symbol):
        symbol = self.symbol_format(symbol)
        
        try:
            info = self.get_exchange_info()['result']
            for pair in info:
                if pair==symbol:
                    return pair["priceIncrement"]
            return {'error':'No matching symbol'}
        except Exception as e:
            return e

    def get_quantity_precision(self,symbol):
        symbol = self.symbol_format(symbol)
        try:
            info = self.get_exchange_info()['result']
            for pair in info:
                if pair['name']==symbol:
                    return pair["sizeIncrement"]
            return {'error':'No matching symbol'}
        except Exception as e:
            return e

    def price(self,symbol):
        symbol = self.symbol_format(symbol)
        try:
            info = self.get_exchange_info()['result']
            for pair in info:
                if pair['name']==symbol:
                    return {'bid':pair["bid"],'ask':pair["ask"]}
            return {'error':'No matching symbol'}
        except Exception as e:
            return e


    def get_balances(self,asset):
        '''Function to get account balances'''
        ts = int(time.time() * 1000)
        request = requests.Request('GET', self.ENDPOINT+'/wallet/balances')
        prepared = request.prepare()
        signature_payload = f'{ts}{prepared.method}{prepared.path_url}'
        if prepared.body:
            signature_payload += prepared.body
        signature_payload = signature_payload.encode()
        signature = hmac.new(self.API_SECRET.encode(), signature_payload, 'sha256').hexdigest()

        request.headers['FTX-KEY'] = self.API_KEY
        request.headers['FTX-SIGN'] = signature
        request.headers['FTX-TS'] = str(ts) 

        response = requests.Session().send(request.prepare()).json()
        if response['success']==True:
            for balance in response['result']:
                if asset==balance['coin']:
                    return balance
        else:
            return response['error']

        
    def get_account_info(self):
        '''Function to get account balances'''
        ts = int(time.time() * 1000)
        request = requests.Request('GET', self.ENDPOINT+'/account')
        prepared = request.prepare()
        signature_payload = f'{ts}{prepared.method}{prepared.path_url}'
        if prepared.body:
            signature_payload += prepared.body
        signature_payload = signature_payload.encode()
        signature = hmac.new(self.API_SECRET.encode(), signature_payload, 'sha256').hexdigest()

        request.headers['FTX-KEY'] = self.API_KEY
        request.headers['FTX-SIGN'] = signature
        request.headers['FTX-TS'] = str(ts) 
        response = requests.Session().send(request.prepare()).json()
        if response['success']==True:
            return response["result"]
        else:
            return response['error']

    def create_market_order(self,symbol,side,quantity):
        symbol = self.symbol_format(symbol)
        '''Function to get account balances'''
        ts = int(time.time() * 1000)
        params = {
            "market":symbol,
            "side":side,
            "price":34,
            "type":"market",
            "size":quantity,
            }
        request = requests.Request('POST', self.ENDPOINT+'/orders',json=params)
        prepared = request.prepare()
        signature_payload = f'{ts}{prepared.method}{prepared.path_url}'+str(params)
        signature_payload = signature_payload.encode()
        signature = hmac.new(self.API_SECRET.encode(), signature_payload, 'sha256').hexdigest()

        request.headers['FTX-KEY'] = self.API_KEY
        request.headers['FTX-SIGN'] = signature
        request.headers['FTX-TS'] = str(ts) 

        response = requests.Session().send(request.prepare()).json()
        if response['success']==True:
            return response["result"]
        else:
            return response['error']


    def create_stop_loss_order(self,symbol,quantity,stopPrice):
        symbol = self.symbol_format(symbol)
        '''Function to create_stop_loss_order'''
        ts = int(time.time() * 1000)
        payload = {
            'market':symbol,
            'side':'sell',
            'type':'stop',
            'size':str(quantity),
            'triggerPrice':str(stopPrice),
            }
        request = requests.Request('POST', self.ENDPOINT+'/orders',payload)
        prepared = request.prepare()
        signature_payload = f'{ts}{prepared.method}{prepared.path_url}'
        if prepared.body:
            signature_payload += prepared.body
        signature_payload = signature_payload.encode()
        signature = hmac.new(self.API_SECRET.encode(), signature_payload, 'sha256').hexdigest()

        request.headers['FTX-KEY'] = self.API_KEY
        request.headers['FTX-SIGN'] = signature
        request.headers['FTX-TS'] = str(ts) 

        response = requests.Session().send(request.prepare()).json()
        if response['success']==True:
            return response["result"]
        else:
            return response['error']
    
    def get_klines_data(self,symbol,interval):
        symbol = self.symbol_format(symbol)
        """Function to get information from candles of 1minute interval
        <time>, <open>, <high>, <low>, <close>, <volume>
        since (1hour for minutes or 1week for days)
        max timeframe is 12hours for minute interval 
        max timeframe is 30 days for hour interval
        max timeframe is 100 weeks for day interval
        """
        if interval=='day':
            interval=86400
        elif interval=='hour':
            interval=3600
        elif interval=='minute':
            interval=60
        else:
            return ('wrong interval')

        limit = 500

        url = self.ENDPOINT+f'/markets/{symbol}/candles?resolution={interval}&limit={limit}'
        response = requests.get(url).json()
        if response['success']==True:
            return response["result"]
        else:
            return response['error']



if __name__=='__main__':
    broker = ftx()
    symbol = 'BTC/USDT'
    broker.connect_key('ftx.key')
    print(broker.get_account_info())
    print(broker.create_market_order('SOLUSDT','sell',1.24652))
    
        