# ！/usr/bin/env python
# _*_ coding:utf-8 _*_

from ccxt.base.exchange import Exchange
import json
from ccxt.base.errors import ExchangeError
from ccxt.base.errors import AuthenticationError
from ccxt.base.errors import OrderNotFound
from ccxt.base.errors import DDoSProtection


class korbitcokr(Exchange):
    token = ''
    tokenType = ''
    refresh_token = ''

    def describe(self):

        return self.deep_extend(super(korbitcokr, self).describe(), {
            'id': 'korbitcokr',
            'name': 'KorbitCoKr',
            'countries': 'KR',  # South Korea
            'version': 'v1',
            'rateLimit': 2000,
            'has': {
                'CORS': False,
                'fetchOHLCV': False,
                'withdraw': True,
                'editOrder': False,
                'fetchOrder': True,
                'fetchOrders': True,
                'fetchOpenOrders': True,
            },
            'urls': {
                'logo': 'https://d3esrl798jsx2v.cloudfront.net/share/logo/logo-landing@2x.png',
                'api': 'https://api.korbit.co.kr',
                'www': 'https://www.korbit.co.kr',
                'doc': 'https://apidocs.korbit.co.kr',
                'fee': 'https://support.korbit.co.kr/customer/ko/portal/articles/2745022',
                'test': 'https://api.korbit-test.com/v1',
            },
            'api': {
                'public': {
                    'get': [
                        'ticker',
                        'ticker/detailed',
                        'orderbook',
                        'transactions',
                        'constants',
                    ],
                    'post': [
                        'oauth2/access_token',
                    ]
                },
                'private': {
                    'post': [
                        'user/orders/buy',
                        'user/orders/sell',
                        'user/orders/cancel',
                        'user/coins/address/assign',
                        'user/coins/out',
                        'user/coins/out/cancel',
                    ],
                    'get': [
                        'user/orders/open',
                        'user/orders',
                        'user/transfers',
                        'user/transactions',
                        'user/volume',
                        'user/balance',
                        'user/accounts',
                        'user/coins/status',
                    ],
                },
            },
        })

    def fetch_markets(self):
        response = self.publicGetConstants()
        result = []
        exchange = response['exchange']
        keys = exchange.keys()
        for key in keys:
            symbolData = exchange[key]
            symbols = key.split('_')
            base = symbols[0]
            quote = symbols[1]
            min_price = symbolData['min_price']
            max_price = symbolData['max_price']
            order_min_size = symbolData['order_min_size']
            order_max_size = symbolData['order_max_size']
            amount_precision = self.get_precision(order_min_size)
            price_precision = self.get_precision(min_price)
            result.append({
                'id': key,
                'symbol': key,
                'base': base,
                'quote': quote,
                'active': True,
                'market': base,
                'precision': {
                    'amount': amount_precision,
                    'price': price_precision,
                },
                'limits': {
                    'amount': {
                        'min': order_min_size,
                        'max': order_max_size,
                    },
                    'price': {
                        'min': min_price,
                        'max': max_price,
                    },
                    'cost': {
                        'min': None,
                        'max': None,
                    },
                },
            })
        return result

    def fetch_order_book(self, symbol):
        self.load_markets()
        market = self.market(symbol)
        request = {
            'currency_pair': market['id'],
        }
        response = self.publicGetOrderbook(self.extend(request))
        return self.parse_order_book(response, None, 'bids', 'asks')

    def fetch_ticker(self, symbol):
        self.load_markets()
        market = self.market(symbol)
        request = {
            'currency_pair': market['id'],
        }
        response = self.publicGetTickerDetailed(self.extend(request))
        timestamp = self.safe_float(response, 'timestamp')
        last = self.safe_float(response, 'last')
        bid = self.safe_float(response, 'bid')
        ask = self.safe_float(response, 'ask')
        low = self.safe_float(response, 'low')
        high = self.safe_float(response, 'high')
        volumne = self.safe_float(response, 'volumne')
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'high': high,
            'low': low,
            'bid': bid,
            'bidVolume': None,
            'ask': ask,
            'askVolume': None,
            'vwap': None,
            'open': None,
            'close': None,
            'last': last,
            'previousClose': None,
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': volumne,
            'quoteVolume': None,
            'info': response,
        }

    def create_order(self, symbol, type, side, amount, price):
        self.load_markets()
        market = self.market(symbol)
        request = {
            'currency_pair': market['id'],
            'type': type,
            'price': str(price),
            'coin_amount': str(amount),
            'nonce': self.milliseconds(),
        }
        response = None
        if side.lower() == 'buy':
            response = self.privatePostUserOrdersBuy(self.extend(request))
        elif side.lower() == 'sell':
            response = self.privatePostUserOrdersSell(self.extend(request))
        if response['status'] == 'success':
            return {
                'id': response['orderId'],
                'info': response,
            }
        else:
            return {
                'info': response
            }

    def cancel_order(self, id, symbol, params={}):
        self.load_markets()
        market = self.market(symbol)
        request = {
            'id': id,
            'currency_pair': market['id'],
            'nonce': self.milliseconds(),
        }
        return self.privatePostUserOrdersCancel(self.extend(request, params))


    def fetch_order(self, id, symbol=None, status=None, offset=None, limit=None, params={}):
        request = {
            'id': id,
        }
        if symbol is not None:
            request['currency_pair'] = symbol
        if status is not None:
            request['status'] = status
        if offset is not None:
            request['offset'] = offset
        if limit is not None:
            request['limint'] = limit

        response = self.privateGetUserOrders(self.extend(request, params))
        return self.parse_orders(response)

    def fetch_open_orders(self, symbol=None, since=0, limit=20, params={}):
        self.load_markets()
        market = self.market(symbol)
        request = {
            'currency_pair': market['id'],
            'offset': since,
            'limit': limit,
        }
        response = self.privateGetUserOrdersOpen(self.extend(request, params))
        return self.parse_orders(response, market, since, limit)

    def fetch_balance(self, prarms={}):
        self.load_markets()
        response = self.privateGetUserBalances()
        result = {'info': response}
        keys = response.keys()
        for key in keys:
            data = response[key]
            fee = self.safe_float(data, 'available')
            trade_in_use = self.safe_float(data, 'trade_in_use')
            withdrawal_in_use = self.safe_float(data, 'withdrawal_in_use')
            account = {
                'fee': fee,
                'used': withdrawal_in_use + trade_in_use,
                'total': fee + withdrawal_in_use + trade_in_use,
            }
            result[key] = account
        return self.parse_balance(result)

    def get_precision(self, num):
        count = 0
        if num < 1 and num > 0:
            while num < 1:
                num *= 10
                count += 1
        if num > 1:
            while num > 1:
                num /= 10
                count += -1
        return count

    def sign(self, path, api='public', method='GET', params={}, headers=None, body=None):
        url = self.urls['api']
        version = self.version
        request = self.implode_params(path, params)
        url += '/' + version + '/' + request
        query = self.omit(params, self.extract_params(path))
        if api == 'public':
            if method == 'GET':
                if query:
                    url += '?' + self.urlencode(query)
            if method == 'POST':
                body = self.json(params)
        else:
            if self.token == '':
                self.create_token_directly()
            else:
                self.refresh_token()
            headers = {
                'Accept': 'application/json',
                'Authorization': '{} {}'.format(self.tokenType, self.token),
            }
            if method == 'GET':
                url += '?' + self.urlencode(params)
            else:
                body = self.json(params)
        return {'url': url, 'method': method, 'body': body, 'headers': headers}

    def create_token_directly(self):
        payload = {
            'client_id': self.apiKey,
            'client_secret': self.secret,
            'username': self.uid,
            'password': self.password,
            'grant_type': "password"
        }
        data = self.publicPostOauth2Access_token(self.extend(payload))
        self.tokenType = data['token_type']
        self.token = data['access_token']
        self.refresh_token = data['refresh_token']
        return self.token

    def refresh_token(self):
        payload = {
            'client_id': self.apiKey,
            'client_secret': self.secret,
            'refresh_token': self.refresh_token,
            'grant_type': "refresh_token"
        }
        data = self.publicPostOauth2Access_token(self.extend(payload))
        self.tokenType = data['token_type']
        self.token = data['access_token']
        self.refresh_token = data['refresh_token']
        return self.token

    def request(self, path, api='public', method='GET', params={}, headers=None, body=None):
        response = self.fetch2(path, api, method, params, headers, body)
        return response

