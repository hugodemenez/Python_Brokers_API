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

    def truncate(number, digits) -> float:
        stepper = 10.0 ** digits
        return math.trunc(stepper * number) / stepper

    def get_server_time(self):
        '''Function to get server time'''
        response = requests.get('https://api.binance.com/api/v3/time',params={}).json()
        try:
            return(int(round(response['serverTime']/1000,0)))
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

    def get_balances(self):
        '''Function to get account balances'''
        try:
            balances=self.account_information()['balances']
        except:
            balances={'error':'unable to get balances'}
        return balances

    def get_open_orders(self):
        '''Function to get open orders'''
        timestamp = self.get_server_time()
        params = {
            'timestamp': timestamp,
        }
        query_string = urlencode(params)
        params['signature'] = hmac.new(self.API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        headers = {'X-MBX-APIKEY': self.API_KEY}
        url = urljoin('https://api.binance.com','/api/v3/openOrderList')
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
        timestamp = int(time.time() * 1000)
        recvWindow=10000
        params = {
            'symbol':symbol,
            'side':side,
            'type':'LIMIT',
            'timeInForce':'GTC',
            'quantity':self.truncate(quantity,6),
            'price':price,
            'timestamp': timestamp,
            'recvWindow':recvWindow,
        }
        query_string = urlencode(params)
        params['signature'] = hmac.new(self.API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        headers = {'X-MBX-APIKEY': self.API_KEY}
        url = urljoin('https://api.binance.com','/api/v3/order')
        response = requests.post(url, headers=headers, params=params).text
        return response

    def create_market_order(self,symbol,side,quantity):
        '''Function to create market order'''
        timestamp = int(time.time() * 1000)
        recvWindow=10000
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
        response = requests.post(url, headers=headers, params=params).text
        return response

    def create_stop_loss_order(self,symbol,quantity,stopPrice,side):
        '''Function to create a stop loss'''
        timestamp = int(time.time() * 1000)
        recvWindow=10000
        params = {
            'symbol':symbol,
            'side':side,
            'type':'STOP_LOSS',
            'timeInForce':'GTC',
            'quantity':self.truncate(quantity,6),
            'price':stopPrice,
            'timestamp': timestamp,
            'recvWindow':recvWindow,
        }
        query_string = urlencode(params)
        params['signature'] = hmac.new(self.API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        headers = {'X-MBX-APIKEY': self.API_KEY}
        url = urljoin('https://api.binance.com','/api/v3/order')
        response = requests.post(url, headers=headers, params=params).text
        return response

    def create_take_profit_order(self,symbol,quantity,profitPrice,side):
        '''Function to create a takeprofit'''
        timestamp = int(time.time() * 1000)
        recvWindow=10000
        params = {
            'symbol':symbol,
            'side':side,
            'type':'TAKE_PROFIT',
            'timeInForce':'GTC',
            'quantity':self.truncate(quantity,6),
            'price':profitPrice,
            'timestamp': timestamp,
            'recvWindow':recvWindow,
        }
        query_string = urlencode(params)
        params['signature'] = hmac.new(self.API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        headers = {'X-MBX-APIKEY': self.API_KEY}
        url = urljoin('https://api.binance.com','/api/v3/order')
        response = requests.post(url, headers=headers, params=params).text
        return response

         
   
class kraken():
    
    '''API development for trading automation in kraken markets with krakenex'''
    def __init__(self):
        self.api=krakenex.API()
 
    def truncate(number, digits) -> float:
            stepper = 10.0 ** digits
            return math.trunc(stepper * number) / stepper
        
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



if __name__=='__main__':
    broker=Python_Brokers_API.binance()

    #Public data
    print(
        broker.price(),
        broker.get_klines_data(),
        broker.get_24h_stats(),
        )

    #To connect api
    print(
        broker.connect_key("binance.key")
    )

    #Private data
    print(
        broker.account_information(),
        broker.get_open_orders(),
        broker.get_balances(),
        broker.create_market_order(symbol='BTCUSD',side='buy',quantity=1),
        broker.create_limit_order(symbol='BTCUSD',side='buy',quantity=1,price=10000),
        broker.create_take_profit_order(symbol='BTCUSD',side='buy',quantity=1,profitPrice=100000),
        broker.create_stop_loss_order(symbol='BTCUSD',side='buy',quantity=1,stopPrice=1000),
    )
