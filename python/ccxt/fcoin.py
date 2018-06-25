# ！/usr/bin/env python
# _*_ coding:utf-8 _*_

'''

@author: yerik

@contact: xiangzz159@qq.com

@time: 2018/6/20 16:04

@desc:

'''

from ccxt.base.exchange import Exchange

# -----------------------------------------------------------------------------

try:
    basestring  # Python 3
except NameError:
    basestring = str  # Python 2
import hashlib
import math
import json
from ccxt.base.errors import ExchangeError
from ccxt.base.errors import InvalidOrder
from ccxt.base.errors import OrderNotFound


class fcoin (Exchange):

    def describe(self):
        return self.deep_extend(super(fcoin, self).describe(), {
            'id': 'fcoin',
            'name': 'FCoin',
            'countries': 'CN',
            'rateLimit': 1000,
            'userAgent': self.userAgents['chrome39'],
            'version': 'v2',
            'accounts': None,
            'accountsById': None,
            'hostname': 'api.fcoin.com',
            'has': {
                'CORS': False,
                'fetchDepositAddress': False,
                'fetchOHCLV': True,
                'fetchOpenOrders': True,
                'fetchClosedOrders': True,
                'fetchOrder': True,
                'fetchOrders': False,
                'fetchTradingLimits': False,
                'withdraw': False,
            },
            'timeframes': {
                '1m': 'M1',
                '3m': 'M3',
                '5m': 'M5',
                '15m': 'M15',
                '30m': 'M30',
                '1h': 'H1',
                '4h': 'H4',
                '6h': 'H6',
                '1d': 'D1',
                '1w': 'W1',
                '1M': '1M',
            },
            'urls': {
                'logo': 'https://www.fcoin.com/static/images/logo_beta.png',
                'api': 'https://api.fcoin.com',
                'www': 'https://www.fcoin.com',
                'doc': 'https://developer.fcoin.com/',
                'fees': 'https://support.fcoin.com/hc/zh-cn/articles/360003715514-%E4%BA%A4%E6%98%93%E6%89%8B%E7%BB%AD%E8%B4%B9%E5%8F%8A%E8%AE%A2%E5%8D%95%E8%A7%84%E5%88%99%E8%AF%B4%E6%98%8E',
            },
            'api': {
                'market': {
                    'get': [
                        'ticker/{symbol}',
                        'depth/{level}/{symbol}',
                        'trades/{symbol}',
                        'candles/{resolution}/{symbol}',
                    ],
                },
                'public': {
                    'get': [
                        'server-time',
                        'currencies',
                        'symbols',
                    ]
                },
                'private': {
                    'get': [
                        'accounts/balance',
                        'orders',
                        'orders/{orderId}',
                        'orders/{orderId}/match_results'
                    ],
                    'post': [
                        'orders',
                        'orders/{orderId}/submit-cancel'
                    ],
                },
            },
            'fees': {
                'trading': {
                    'tierBased': False,
                    'percentage': True,
                    'maker': 0.001,
                    'taker': 0.001,
                },
            },
        })

    def parse_markets(self, markets):
        numMarkets = len(markets)
        if numMarkets < 1:
            raise ExchangeError(self.id + ' publicGetCommonSymbols returned empty response: ' + self.json(markets))
        result = []
        for i in range(0, len(markets)):
            market = markets[i]
            baseId = market['base_currency']
            quoteId = market['quote_currency']
            price_decimal = market['price_decimal']
            amount_decimal = market['amount_decimal']
            base = baseId.upper()
            quote = quoteId.upper()
            id = baseId + quoteId
            base = self.common_currency_code(base)
            quote = self.common_currency_code(quote)
            symbol = base + '/' + quote
            precision = {
                'amount': amount_decimal,
                'price': price_decimal,
            }
            lot = math.pow(10, -precision['amount'])
            maker = 0 if (base == 'OMG') else 0.2 / 100
            taker = 0 if (base == 'OMG') else 0.2 / 100
            result.append({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'lot': lot,
                'precision': precision,
                'taker': taker,
                'maker': maker,
                'limits': {
                    'amount': {
                        'min': lot,
                        'max': math.pow(10, precision['amount']),
                    },
                    'price': {
                        'min': math.pow(10, -precision['price']),
                        'max': None,
                    },
                    'cost': {
                        'min': 0,
                        'max': None,
                    },
                },
                'info': market,
            })
        return result

    def fetch_markets(self):
        response = self.publicGetSymbols()
        return self.parse_markets(response['data'])

    def fetch_ticker(self, symbol, params={}):
        self.load_markets()
        market = self.market(symbol)
        response = self.marketGetTickerSymbol(self.extend({
            'symbol': market['id'],
        }, params))
        return self.parse_ticker(response['data'], market)

    def parse_ticker(self, data, market=None):
        symbol = None
        if market:
            symbol = market['symbol']
        timestamp = self.milliseconds()
        ticker = data['ticker']
        bid = float(ticker[2])
        bidVolume = float(ticker[3])
        ask = float(ticker[4])
        askVolume = float(ticker[5])
        last = float(ticker[0])
        high = float(ticker[7])
        low = float(ticker[8])
        open = None
        close = None
        change = None
        percentage = None
        average = None
        baseVolume = float(ticker[9])
        quoteVolume = float(ticker[10])
        vwap = None
        if baseVolume is not None and quoteVolume is not None and baseVolume > 0:
            vwap = quoteVolume / baseVolume
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'high': high,
            'low': low,
            'bid': bid,
            'bidVolume': bidVolume,
            'ask': ask,
            'askVolume': askVolume,
            'vwap': vwap,
            'open': open,
            'close': close,
            'last': last,
            'previousClose': None,
            'change': change,
            'percentage': percentage,
            'average': average,
            'baseVolume': baseVolume,
            'quoteVolume': quoteVolume,
            'info': data,
        }

    def parse_bids_asks(self, bidasks, price_key=0, amount_key=1):
        result = []
        if len(bidasks):
            for i in range(0, int(len(bidasks) / 2)):
                result.append([bidasks[2 * i + 0], bidasks[2 * i + 1]])
        return result

    def fetch_order_book(self, symbol, limit=None, params={}):
        self.load_markets()
        market = self.market(symbol)
        limit = 'L20' if limit is None else 'L' + str(limit)
        response = self.marketGetDepthLevelSymbol(self.extend({
            'symbol': market['id'],
            'level': limit,
        }, params))
        order_book = response['data']
        ts = order_book['ts']
        return self.parse_order_book(order_book, ts)

    def fetch_trades(self, symbol, since=None, limit=20, params={}):
        self.load_markets()
        market = self.market(symbol)
        request = {
            'symbol': market['id'],
            'limit': limit
        }
        if since is not None:
            request['before'] = since
        response = self.marketGetTradesSymbol(self.extend(request, params))
        trades = response['data']
        result = []
        for trade in trades:
            result.append(self.parse_trade(trade, market))
        result = self.sort_by(result, 'timestamp')
        return self.filter_by_symbol_since_limit(result, symbol, since, limit)

    def parse_trade(self, trade, market):
        timestamp = trade['ts']
        return {
            'info': trade,
            'id': str(trade['id']),
            'order': None,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': market['symbol'],
            'type': None,
            'side': trade['side'],
            'price': trade['price'],
            'amount': trade['amount'],
        }

    def parse_ohlcv(self, ohlcv, market=None, timeframe='5m', since=None, limit=None):
        return [
            ohlcv['id'] * 1000,
            ohlcv['open'],
            ohlcv['high'],
            ohlcv['low'],
            ohlcv['close'],
            ohlcv['quote_vol'],
        ]

    def fetch_ohlcv(self, symbol, timeframe='5m', since=None, limit=20, params={}):
        self.load_markets()
        market = self.market(symbol)
        request = {
            'symbol': market['id'],
            'resolution': self.timeframes[timeframe],
            'limit': limit,
        }
        if since is not None:
            request['before'] = since
        if limit is not None:
            request['size'] = limit
        response = self.marketGetCandlesResolutionSymbol(self.extend(request, params))
        return self.parse_ohlcvs(response['data'], market, timeframe, since, limit)

    def fetch_balance(self, params={}):
        self.load_markets()
        response = self.privateGetAccountsBalance()
        balances = response['data']
        result = {'info': response}
        for balance in balances:
            uppercase = balance['currency'].upper()
            currency = self.common_currency_code(uppercase)
            account = dict()
            account['free'] = balance['available']
            account['used'] = balance['frozen']
            account['total'] = balance['balance']
            result[currency] = account
        return self.parse_balance(result)

    def fetch_orders(self, symbol=None, since=None, limit=None, params={}):
        self.load_markets()
        market = self.market(symbol)
        limit = 20 if limit is None else limit
        request = {
            'limit': limit
        }
        if symbol is not None:
            request['symbol'] = market['id']
        if since is not None:
            request['after'] = since

        response = self.privateGetOrders(self.extend(request, params))
        return self.parse_orders(response['data'], market, since, limit)

    def fetch_order(self, id, symbol=None, params={}):
        self.load_markets()
        market = self.market(symbol)
        response = self.privateGetOrderOrdersId(self.extend({
            'order_id': id,
        }, params))
        return self.parse_order(response['data'], market)

    def parse_order(self, order, market=None):
        side = order['side']
        type = order['type']
        status = self.parse_order_status(order['state'])
        symbol = None
        if not market:
            if 'symbol' in order:
                if order['symbol'] in self.markets_by_id:
                    marketId = order['symbol']
                    market = self.markets_by_id[marketId]
        if market:
            symbol = market['symbol']
        timestamp = order['created_at']
        amount = float(order['amount'])
        filled = float(order['field_amount'])
        remaining = amount - filled
        price = float(order['price'])
        cost = float(order['executed_value'])
        fee = float(order['fill_fees'])
        average = 0
        if filled > 0:
            average = float(cost / filled)
        result = {
            'info': order,
            'id': str(order['id']),
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': symbol,
            'type': type,
            'side': side,
            'price': price,
            'average': average,
            'cost': cost,
            'amount': amount,
            'filled': filled,
            'remaining': remaining,
            'status': status,
            'fee': fee,
        }
        return result

    def parse_order_status(self, status):
        if status == 'partial_filled':
            return 'open'
        elif status == 'partial_canceled':
            return 'canceled'
        elif status == 'filled':
            return 'closed'
        elif status == 'canceled':
            return 'canceled'
        elif status == 'submitted':
            return 'open'
        elif status == 'pending_cancel':
            return 'open'
        return status

    def create_order(self, symbol, type, side, amount, price=None, params={}):
        self.load_markets()
        market = self.market(symbol)
        order = {
            'amount': self.amount_to_precision(symbol, amount),
            'symbol': market['id'],
            'type': type,
            'side': side,
        }
        if type == 'limit':
            order['price'] = self.price_to_precision(symbol, price)
        response = self.privatePostOrders(self.extend(order, params))
        return {
            'info': response,
            'id': response['data'],
        }

    def cancel_order(self, id, symbol=None, params={}):
        return self.privatePostOrdersOrderIdSubmitCancel({'order_id': id})

    def get_signed(self, sig_str):
        """signed params use sha512"""
        sig_str = base64.b64encode(sig_str)
        signature = base64.b64encode(hmac.new(bytes(self.secret, 'utf-8'), sig_str, digestmod=hashlib.sha1).digest())
        return signature

    def sign(self, path, api='public', method='GET', params={}, headers=None, body=None):
        if api == 'private':
            url = '/' + self.version
        else:
            url = '/' + self.version + '/' + api

        url += '/' + self.implode_params(path, params)
        query = self.omit(params, self.extract_params(path))
        if api == 'private':
            self.check_required_credentials()
            param = ''
            if params != {}:
                sort_pay = sorted(params.items())
                # sort_pay.sort()
                for k in sort_pay:
                    param += '&' + str(k[0]) + '=' + str(k[1])
                param = param.lstrip('&')
            timestamp = str(int(time.time() * 1000))
            full_url = self.urls['api'] + url

            if method == 'GET':
                if param:
                    full_url = full_url + '?' + param
                sig_str = method + full_url + timestamp
            elif method == 'POST':
                sig_str = method + full_url + timestamp + param

            signature = self.get_signed(bytes(sig_str, 'utf-8'))

            headers = {
                'FC-ACCESS-KEY': self.apiKey,
                'FC-ACCESS-SIGNATURE': signature.decode(),
                'FC-ACCESS-TIMESTAMP': timestamp
            }

            if method == 'POST':
                body = self.json(query)
                headers['Content-Type'] = 'application/json'
        else:
            if params:
                url += '?' + self.urlencode(params)
        url = self.urls['api'] + url
        return {'url': url, 'method': method, 'body': body, 'headers': headers}