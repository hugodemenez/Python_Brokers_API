r"""
Module pour faire des implémentations dans des robots de trading pour automatiser et faciliter le passage
d'ordre sur les brokers crypto
"""

__author__ = 'Hugo Demenez <hdemenez@hotmail.fr>'

import time,json,hmac,hashlib,requests,krakenex
from urllib.parse import urljoin, urlencode


class binance():
    '''Développement API pour automatisation d'echanges sur les marchés de binance'''
    def __init__(self):
        self.API_SECRET=''
        self.API_KEY=''

    def get_klines_data(self,symbol):
        '''Fonction pour obtenir les informations des bougies d'interval 1minute [Open time,Open,High,Low,Close,Volume,Close time,
        Quote asset volume,Number of trades,Taker buy base asset volume,Taker buy quote asset volume,Ignore.]
        '''
        response = requests.get('https://api.binance.com/api/v3/klines',params={'symbol':symbol,'interval':'1m'}).json()
        return response

    def get_24h_stats(self,symbol):
        '''Fonction pour obtenir les statsistiques des dernières 24h'''
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
        
    def connect_key(self,path):
        '''Fonction pour connecter l'api au compte'''
        try:
            with open(path, 'r') as f:
                self.API_KEY = f.readline().strip()
                self.API_SECRET = f.readline().strip()
            return ("Successfuly connected your keys")
        except:
            return ("Unable to read .key file")
        
    def price(self,symbol):
        '''Fonction pour obtenir les prix du symbol'''
        response = requests.get('https://api.binance.com/api/v3/ticker/bookTicker',params={'symbol':symbol}).json()
        try:
            bid=float(response['bidPrice'])
            ask=float(response['askPrice'])
            price={'bid':bid,'ask':ask}
        except:
            return response['msg']
        return price

    def account_information(self):
        '''Fonction pour obtenir les informations du compte'''
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

    def create_limit_order(self,symbol,side,price,quantity):
        '''Fonction pour créer un ordre limite'''
        timestamp = int(time.time() * 1000)
        recvWindow=10000
        params = {
            'symbol':symbol,
            'side':side,
            'type':'LIMIT',
            'timeInForce':'GTC',
            'quantity':round(quantity,6),
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
        '''Fonction pour créer un ordre au marché'''
        timestamp = int(time.time() * 1000)
        recvWindow=10000
        params = {
            'symbol':symbol,
            'side':side,
            'type':'MARKET',
            'quantity':round(quantity,6),
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
        '''Fonction pour créer un stop loss'''
        timestamp = int(time.time() * 1000)
        recvWindow=10000
        params = {
            'symbol':symbol,
            'side':side,
            'type':'STOP_LOSS',
            'timeInForce':'GTC',
            'quantity':round(quantity,6),
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
        '''Fonction pour créer un takeprofit'''
        timestamp = int(time.time() * 1000)
        recvWindow=10000
        params = {
            'symbol':symbol,
            'side':side,
            'type':'TAKE_PROFIT',
            'timeInForce':'GTC',
            'quantity':round(quantity,6),
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

    def get_balances(self):
        '''Fonction pour récuperer les soldes des portefeuilles'''
        try:
            balances=self.account_information()['balances']
        except:
            balances={'error':'unable to get balances'}
        return balances

    def get_open_orders(self):
        '''Fonction pour récuperer les ordres ouverts'''
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
         
    def get_server_time(self):
        '''Fonction pour obtenir l'heure du serveur '''
        response = requests.get('https://api.binance.com/api/v3/time',params={}).json()
        try:
            return(response['serverTime'])
        except:
            return('unable to get server time')
        
class kraken():
    '''Développement API pour automatisation d'echanges sur les marchés de kraken avec krakenex'''
    def __init__(self):
        self.api=krakenex.API()
 
    def get_24h_stats(self,symbol):
        '''Fonction pour obtenir les statistiques des dernières 24h'''
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

    def get_klines_data(self,symbol):
        '''Fonction pour obtenir les informations des bougies d'interval 1minute
        <time>, <open>, <high>, <low>, <close>, <vwap>, <volume>, <count>
        '''
        response = requests.get('https://api.kraken.com/0/public/OHLC',params={'pair':symbol,'interval':'1'}).json()
        return response

    def connect_key(self,path):
        '''Fonction pour connecter l'api au compte'''
        self.api.load_key(path=path)

    def price(self,symbol):
        '''Fonction pour obtenir les prix du symbol'''
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
        '''Fonction pour obtenir les informations du compte'''
        try:
            informations = self.api.query_private(method="Balance")['result']
        except:
            informations={'error':'unable to get informations'}
        return informations

    def get_balances(self):
        '''Fonction pour récuperer les soldes des portefeuilles'''
        try:
            balances = self.api.query_private(method="Balance")['result']
        except:
            balances={'error':'unable to get balances'}
        return balances

    def get_open_orders(self):
        '''Fonction pour récuperer les ordres ouverts'''
        try:
            open_orders= self.api.query_private(method='OpenOrders')
            open_orders=open_orders['result']['open']
        except:
            return ('unable to get open orders')
        return open_orders

    def create_stop_loss_order(self,symbol,quantity,stopPrice,side):
        '''Fonction pour créer un stop loss'''
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

    def create_market_order(self,symbol,side,quantity):
        '''Fonction pour créer un ordre au marché'''
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

    def create_take_profit_order(self,symbol,quantity,profitPrice,side):
        '''Fonction pour créer un takeprofit'''
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

    def create_limit_order(self,symbol,side,price,quantity):
        '''Fonction pour créer un ordre limite'''
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

    def get_server_time(self):
        '''Fonction pour obtenir l'heure du serveur '''
        response = requests.get('https://api.kraken.com/0/public/Time',params={}).json()
        try:
            return(response['result']['unixtime'])
        except:
            return('unable to get server time')
        

if __name__=='__main__':
    pass
