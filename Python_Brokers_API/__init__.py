r"""
Python functions for crypto-brokers API
"""

__author__ = 'Hugo Demenez <hdemenez@hotmail.fr>'

import time,json,hmac,hashlib,requests,krakenex,math
from urllib.parse import urljoin, urlencode


class binance():
    '''API development for trade automation in binance markets'''
    def __init__(self):
        self.API_SECRET=''
        self.API_KEY=''

    def truncate(self,number, digits) -> float:
        stepper = 10.0 ** digits
        return math.trunc(stepper * number) / stepper

    def create_key_file(self): 
        """Function to create your .key file"""
        API_KEY = str(input("Enter your API key :"))
        SECRET_KEY = str(input("Enter your SECRET_KEY :"))
        file = open("binance.key","w")
        file.write(API_KEY+'\n')
        file.write(SECRET_KEY)
        file.close()

    def get_server_time(self):
        '''Function to get server time'''
        response = requests.get('https://api.binance.com/api/v3/time',params={}).json()
        try:
            return response['serverTime']
        except:
            return('unable to get server time')
     
    def get_24h_stats(self,symbol):
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
        '''Function to create a limit order'''
        timestamp = self.get_server_time()
        recvWindow=10000
        params = {
            'symbol':symbol,
            'side':side,
            'type':'LIMIT',
            'timeInForce':'GTC',
            'quantity':self.truncate(quantity,6),
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
                'quoteOrderQty':self.truncate(quantity,6),
                'timestamp': timestamp,
                'recvWindow':recvWindow,
            }
        elif side=='sell':
            params = {
                'symbol':symbol,
                'side':side,
                'type':'MARKET',
                'quantity':self.truncate(quantity,6),
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
        '''Function to create a stop loss'''
        timestamp = self.get_server_time()
        recvWindow=10000
        params = {
            'symbol':symbol,
            'side':'sell',
            'type':'STOP_LOSS_LIMIT',
            'timeInForce':'GTC',
            'quantity':self.truncate(quantity,6),
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
        '''Function to create a take profit order (limit sell)'''
        timestamp = self.get_server_time()
        recvWindow=10000
        params = {
            'symbol':symbol,
            'side':'sell',
            'type':'LIMIT',
            'timeInForce':'GTC',
            'quantity':self.truncate(quantity,6),
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


class kraken():
    
    '''API development for trading automation in kraken markets with krakenex'''
    def __init__(self):
        self.api=krakenex.API()
 
    def truncate(self,number, digits) -> float:
            stepper = 10.0 ** digits
            return math.trunc(stepper * number) / stepper

    def create_key_file(self): 
        """Function to create your .key file"""
        API_KEY = str(input("Enter your API key :"))
        SECRET_KEY = str(input("Enter your SECRET_KEY :"))
        file = open("kraken.key","w")
        file.write(API_KEY+'\n')
        file.write(SECRET_KEY)
        file.close()

    def get_server_time(self):
        '''Function to get server time'''
        response = requests.get('https://api.kraken.com/0/public/Time',params={}).json()
        try:
            return(response['result']['unixtime'])
        except:
            return('unable to get server time')

    def get_24h_stats(self,symbol):
        '''Function to get statistics for the last 24h'''
        response = requests.get('https://api.kraken.com/0/public/Ticker',params={'pair':symbol}).json()
        
        try:
            for symbol in response['result']:
                stats={
                    'volume':response['result'][symbol]['v'][1],
                    'open':response['result'][symbol]['o'],
                    'high':response['result'][symbol]['h'][1],
                    'low':response['result'][symbol]['l'][1],
                    'last':response['result'][symbol]['c'][0],
                }
        except:
            stats={
                'error':response,
            }
        finally:
            return stats

    def get_klines_data(self,symbol,interval):
        '''Function to get information from candles of 1minute interval
        <time>, <open>, <high>, <low>, <close>,<volume>
        since (1hour for minutes or 1week for days)
        max timeframe is 12hours for minute interval 
        max timeframe is 30 days for hour interval
        max timeframe is 100 weeks for day interval
        '''
        if interval=='day':
            interval='1440'

        elif interval=='hour':
            interval='60'

        elif interval=='minute':
            interval='1'

        else:
            return ('wrong interval')
        response = requests.get('https://api.kraken.com/0/public/OHLC',params={'pair':symbol,'interval':interval}).json()
        try :
            for pair in response['result']:
                if pair=='last':
                    pair=pair1
                pair1=pair
            reponse = response['result'][pair]
            formated_response=[]
            for info in reponse:
                data={}
                data['time']=info[0]
                data['open']=float(info[1])
                data['high']=float(info[2])
                data['low']=float(info[3])
                data['close']=float(info[4])
                data['volume']=float(info[6])
                formated_response.append(data)
        except:
            formated_response = response['error']
        return formated_response

    def connect_key(self,path):
        '''Function to connect the api to the account'''
        self.api.load_key(path=path)

    def price(self,symbol):
        '''Function to get symbol prices'''
        response = requests.get('https://api.kraken.com/0/public/Ticker',params={'pair':symbol}).json()
        
        try:
            for name in response['result']:
                bid=float(response['result'][name]['b'][0])
                ask=float(response['result'][name]['a'][0])
                price={'bid':bid,'ask':ask}
        except:
            return response['error']
        return price

    def account_information(self):
        '''Function to get account information'''
        try:
            informations = self.api.query_private(method="Balance")['result']
        except:
            informations={'error':'unable to get informations'}
        return informations

    def get_balances(self):
        '''Function to get account balances'''
        try:
            balances = self.api.query_private(method="Balance")['result']
        except:
            balances={'error':'unable to get balances'}
        return balances

    def get_open_orders(self):
        '''Function to get open orders'''
        try:
            open_orders= self.api.query_private(method='OpenOrders')
            open_orders=open_orders['result']['open']
        except:
            return ('unable to get open orders')
        return open_orders

    def create_limit_order(self,symbol,side,price,quantity):
        '''Function to create a limit order'''
        data={
            'pair':symbol,
            'ordertype':'limit',
            'type':side,
            'volume':quantity,
            'price':price,
        }
        #On essaie de transmettre l'ordre au marché
        try :
            ordre = self.api.query_private(method='AddOrder',data=data)
        except:
            return ('unable to join market')
        return ordre

    def create_market_order(self,symbol,side,quantity):
        '''Function to create market order'''
        data={
            'pair':symbol,
            'ordertype':'market',
            'type':side,
            'volume':quantity,
        }
        #On essaie de transmettre l'ordre au marché
        try :
            ordre = self.api.query_private(method='AddOrder',data=data)
        except:
            return ('unable to join market')
        return ordre

    def create_stop_loss_order(self,symbol,quantity,stopPrice,side):
        '''Function to create a stop loss'''
        data={
            'pair':symbol,
            'ordertype':'stop-loss',
            'type':side,
            'volume':quantity,
            'price':stopPrice,
        }
        #On essaie de transmettre l'ordre au marché
        try :
            ordre = self.api.query_private(method='AddOrder',data=data)
        except:
            return ('unable to join market')
        return ordre

    def create_take_profit_order(self,symbol,quantity,profitPrice,side):
        '''Function to create a takeprofit'''
        data={
            'pair':symbol,
            'ordertype':'take-profit',
            'type':side,
            'volume':quantity,
            'price':profitPrice,
        }
        #On essaie de transmettre l'ordre au marché
        try :
            ordre = self.api.query_private(method='AddOrder',data=data)
        except:
            return ('unable to join market')
        return ordre

    def test_order(self):
        '''Function to create test order'''
        data={
            'pair':'BTCEUR',
            'ordertype':'market',
            'type':'buy',
            'volume':1,
            'validate':1,
        }
        #On essaie de transmettre l'ordre au marché
        try :
            ordre = self.api.query_private(method='AddOrder',data=data)
            if ordre["error"]==[]:
                return True
            else:
                return False
        except:
            return False
        



if __name__=='__main__':
    pass
        