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


import hmac
import time
import urllib.parse
from typing import Optional, Dict, Any, List

from ciso8601 import parse_datetime
from requests import Request, Session, Response


class ftx:
    def __init__(
        self,
        base_url: str = "https://ftx.com/api/",
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        subaccount_name: Optional[str] = None,
    ) -> None:
        self._session = Session()
        self._base_url = base_url
        self._api_key = api_key
        self._api_secret = api_secret
        self._subaccount_name = subaccount_name

    def symbol_format(self,symbol):
        return re.sub("[^0-9a-zA-Z]+", "/", symbol)


    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('GET', path, params=params)

    def _post(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('POST', path, json=params)

    def _delete(self,
                path: str,
                params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('DELETE', path, json=params)

    def _request(self, method: str, path: str, **kwargs) -> Any:
        request = Request(method, self._base_url + path, **kwargs)
        if self._api_key:
            self._sign_request(request)
        response = self._session.send(request.prepare())

        return self._process_response(response)

    def _sign_request(self, request: Request) -> None:
        ts = int(time.time() * 1000)
        prepared = request.prepare()
        signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode(
        )
        if prepared.body:
            signature_payload += prepared.body
        signature = hmac.new(self._api_secret.encode(), signature_payload,
                             'sha256').hexdigest()
        request.headers['FTX-KEY'] = self._api_key
        request.headers['FTX-SIGN'] = signature
        request.headers['FTX-TS'] = str(ts)
        if self._subaccount_name:
            request.headers['FTX-SUBACCOUNT'] = urllib.parse.quote(
                self._subaccount_name)

    @staticmethod
    def _process_response(response: Response) -> Any:
        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            raise
        else:
            if not data['success']:
                raise Exception(data['error'])
            return data['result']

    #
    # Authentication required methods
    #
    def authentication_required(fn):
        """Annotation for methods that require auth."""
        def wrapped(self, *args, **kwargs):
            if not self._api_key:
                raise TypeError("You must be authenticated to use this method")
            else:
                return fn(self, *args, **kwargs)

        return wrapped

    @authentication_required
    def get_account_info(self) -> dict:
        return self._get('account')

    @authentication_required
    def get_open_orders(self, market: Optional[str] = None) -> List[dict]:
        return self._get('orders', {'market': self.symbol_format(market)})

    @authentication_required
    def get_order_status(self, existing_order_id: int) -> dict:
        return self._get(f'orders/{existing_order_id}')

    @authentication_required
    def get_order_history(self,
                          market: Optional[str] = None,
                          side: Optional[str] = None,
                          order_type: Optional[str] = None,
                          start_time: Optional[float] = None,
                          end_time: Optional[float] = None) -> List[dict]:
        return self._get(
            'orders/history', {
                'market': self.symbol_format(market),
                'side': side,
                'orderType': order_type,
                'start_time': start_time,
                'end_time': end_time
            })

    @authentication_required
    def get_conditional_order_history(
            self,
            market: Optional[str] = None,
            side: Optional[str] = None,
            type: Optional[str] = None,
            order_type: Optional[str] = None,
            start_time: Optional[float] = None,
            end_time: Optional[float] = None) -> List[dict]:
        return self._get(
            'conditional_orders/history', {
                'market': self.symbol_format(market),
                'side': side,
                'type': type,
                'orderType': order_type,
                'start_time': start_time,
                'end_time': end_time
            })

    @authentication_required
    def modify_order(
        self,
        existing_order_id: Optional[str] = None,
        existing_client_order_id: Optional[str] = None,
        price: Optional[float] = None,
        size: Optional[float] = None,
        client_order_id: Optional[str] = None,
    ) -> dict:
        assert (existing_order_id is None) ^ (existing_client_order_id is None), \
            'Must supply exactly one ID for the order to modify'
        assert (price is None) or (size is
                                   None), 'Must modify price or size of order'
        path = f'orders/{existing_order_id}/modify' if existing_order_id is not None else \
            f'orders/by_client_id/{existing_client_order_id}/modify'
        return self._post(
            path, {
                **({
                    'size': size
                } if size is not None else {}),
                **({
                    'price': price
                } if price is not None else {}),
                **({
                    'clientId': client_order_id
                } if client_order_id is not None else {}),
            })

    @authentication_required
    def get_conditional_orders(self,
                               market: Optional[str] = None) -> List[dict]:
        return self._get('conditional_orders', {'market': self.symbol_format(market)})

    @authentication_required
    def place_order(self,
                    market: str,
                    side: str,
                    price: float,
                    size: float,
                    type: str = 'limit',
                    reduce_only: bool = False,
                    ioc: bool = False,
                    post_only: bool = False,
                    client_id: Optional[str] = None) -> dict:
        return self._post(
            'orders', {
                'market': self.symbol_format(market),
                'side': side,
                'price': price,
                'size': size,
                'type': type,
                'reduceOnly': reduce_only,
                'ioc': ioc,
                'postOnly': post_only,
                'clientId': client_id,
            })

    @authentication_required
    def place_conditional_order(self,
                                market: str,
                                side: str,
                                size: float,
                                type: str,
                                limit_price: Optional[float] = None,
                                reduce_only: bool = False,
                                cancel: bool = True,
                                trigger_price: Optional[float] = None,
                                trail_value: Optional[float] = None) -> dict:
        """
        To send a Stop Market order, set type='stop' and supply a trigger_price
        To send a Stop Limit order, also supply a limit_price
        To send a Take Profit Market order, set type='trailing_stop' and supply a trigger_price
        To send a Trailing Stop order, set type='trailing_stop' and supply a trail_value
        """
        assert type in ('stop', 'take_profit', 'trailing_stop')
        assert type not in ('stop', 'take_profit') or trigger_price is not None, \
            'Need trigger prices for stop losses and take profits'
        assert type not in ('trailing_stop',) or (trigger_price is None and trail_value is not None), \
            'Trailing stops need a trail value and cannot take a trigger price'

        return self._post(
            'conditional_orders', {
                'market': self.symbol_format(market),
                'side': side,
                'triggerPrice': trigger_price,
                'size': size,
                'reduceOnly': reduce_only,
                'type': type,
                'cancelLimitOnTrigger': cancel,
                'orderPrice': limit_price
            })

    @authentication_required
    def cancel_order(self, order_id: str) -> dict:
        return self._delete(f'orders/{order_id}')

    @authentication_required
    def cancel_orders(self,
                      market_name: Optional[str] = None,
                      conditional_orders: bool = False,
                      limit_orders: bool = False) -> dict:
        return self._delete(
            'orders', {
                'market': self.symbol_format(market_name),
                'conditionalOrdersOnly': conditional_orders,
                'limitOrdersOnly': limit_orders,
            })

    @authentication_required
    def get_fills(self) -> List[dict]:
        return self._get('fills')



    @authentication_required
    def get_deposit_address(self,
                            ticker: str,
                            method: Optional[str] = None) -> dict:
        method = f'?method={method}' if method else ''
        return self._get(f'wallet/deposit_address/{ticker}{method}')

    @authentication_required
    def get_positions(self, show_avg_price: bool = False) -> List[dict]:
        return self._get('positions', {'showAvgPrice': show_avg_price})

    @authentication_required
    def get_position(self, name: str, show_avg_price: bool = False) -> dict:
        return next(
            filter(lambda x: x['future'] == name,
                   self.get_positions(show_avg_price)), None)

    @authentication_required
    def set_leverage(self, leverage):
        return self._post('account/leverage', {'leverage': leverage})

    @authentication_required
    def get_subaccounts(self) -> List[dict]:
        return self._get('subaccounts')

    @authentication_required
    def create_subaccounts(self, nickname) -> List[dict]:
        return self._post('subaccounts', {'nickname': nickname})

    @authentication_required
    def delete_subaccounts(self, nickname: Optional[str] = None) -> List[dict]:
        assert (nickname is not None) or (self._subaccount_name
                                          is not None), 'SubAccount not set'
        subaccount = nickname or self._subaccount_name
        return self._delete('subaccounts', {'nickname': subaccount})

    @authentication_required
    def get_subaccounts_balance(self, nickname=None) -> List[dict]:
        assert (nickname is not None) or (self._subaccount_name
                                          is not None), 'SubAccount not set'
        subaccount = nickname or self._subaccount_name
        return self._get(f'subaccounts/{subaccount}/balances',
                         {'nickname': subaccount})

    @authentication_required
    def request_quote(self, fromCoin, toCoin, size) -> List[dict]:
        return self._post('otc/quotes', {
            'fromCoin': fromCoin,
            'toCoin': toCoin,
            'size': size
        })

    @authentication_required
    def get_quote_details(self, quoteId):
        return self._get(f'otc/quotes/{quoteId}')

    @authentication_required
    def accept_quote(self, quoteId):
        return self._post(f'otc/quotes/{quoteId}/accept')

    @authentication_required
    def request_withdrawal(self,
                           coin: str,
                           size: float,
                           address: str,
                           password: Optional[str] = None,
                           code: Optional[str] = None):
        assert (size > 0), 'Size must be greater than 0'
        return self._post('wallet/withdrawals', {
            'coin': coin,
            'size': size,
            'address': address
        })

    #
    # Public methods
    #

    def get_futures(self) -> List[dict]:
        return self._get('futures')

    def get_future(self, future_name: str) -> dict:
        return self._get(f'futures/{future_name}')

    def get_markets(self) -> List[dict]:
        return self._get('markets')

    def get_market(self, market: str) -> dict:
        return self._get(f'markets/{market}')

    def get_orderbook(self, market: str, depth: Optional[int] = None) -> dict:
        return self._get(f'markets/{market}/orderbook', {'depth': depth})

    def get_trades(self,
                   market: str,
                   limit: int = 100,
                   start_time: Optional[float] = None,
                   end_time: Optional[float] = None) -> dict:
        return self._get(f'markets/{market}/trades', {
            'limit': limit,
            'start_time': start_time,
            'end_time': end_time
        })

    def get_all_trades(self,
                       market: str,
                       start_time: Optional[float] = None,
                       end_time: Optional[float] = None) -> List:
        ids = set()
        limit = 100
        results = []
        while True:
            response = self._get(f'markets/{self.symbol_format(market)}/trades', {
                'end_time': end_time,
                'start_time': start_time,
            })
            deduped_trades = [r for r in response if r['id'] not in ids]
            results.extend(deduped_trades)
            ids |= {r['id'] for r in deduped_trades}
            print(f'Adding {len(response)} trades with end time {end_time}')
            if len(response) == 0:
                break
            end_time = min(parse_datetime(t['time'])
                           for t in response).timestamp()
            if len(response) < limit:
                break
        return results

    def get_historical_data(self, market_name: str, resolution: int,
                            limit: int, start_time: float,
                            end_time: float) -> dict:
        return self._get(
            f'markets/{market_name}/candles',
            dict(resolution=resolution,
                 limit=limit,
                 start_time=start_time,
                 end_time=end_time))

    def get_future_stats(self, future_name) -> List[dict]:
        return self._get(f'futures/{future_name}/stats',
                         {'future_name': future_name})

    def get_funding_rates(self, future: Optional[str] = None,
                                start_time: Optional[float] = None,
                                end_time: Optional[float] = None) -> List[dict]:
        return self._get('funding_rates',
            dict(future=future,
                start_time=start_time,
                end_time=end_time))



    def connect_key(self,path):
        '''Function to connect the api to the account'''
        try:
            with open(path, 'r') as f:
                self._api_key = f.readline().strip()
                self._api_secret = f.readline().strip()
            return ("Successfuly connected your keys")
        except:
            return ("Unable to read .key file")

    def create_key_file(self): 
        """Function to create your .key file"""
        _api_key = str(input("Enter your API key :"))
        _api_secret = str(input("Enter your SECRET_KEY :"))
        file = open("ftx.key","w")
        file.write(_api_key+'\n')
        file.write(_api_secret)
        file.close()
        return True



    def get_exchange_info(self):
        '''Function to get server time'''
        response = requests.get(self._base_url+'/markets',params={}).json()
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


    def get_balances(self,asset) -> dict:
        '''Function to get account balances'''
        response = self._get('wallet/balances')
        try:
            for balance in response:
                if asset==balance['coin']:
                    return balance
        except:
            return 


    def create_market_order(self,symbol,side,quantity):
        symbol = self.symbol_format(symbol)
        return self.place_order(symbol,side,0,quantity,"market")


    def create_stop_loss_order(self,symbol,quantity,stopPrice):
        symbol = self.symbol_format(symbol)
        return self.place_conditional_order(symbol,"sell",quantity,"stop",trigger_price=stopPrice)

    
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

        limit = 720

        url = self._base_url+f'/markets/{symbol}/candles?resolution={interval}&limit={limit}'
        response = requests.get(url).json()
        if response['success']==True:
            return response["result"]
        else:
            return response['error']

    def cancel_all_orders(self,symbol):
        symbol = self.symbol_format(symbol)
        return self.cancel_orders(symbol,True)

    def test_order(self):
        try:
            self.get_account_info()
            return True
        except:
            return False


if __name__=='__main__':
    broker = ftx()
    symbol = 'BTC*USDT'
    broker.connect_key('ftx.key')
    print(broker.test_order())
    
        