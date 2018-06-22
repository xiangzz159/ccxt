# ！/usr/bin/env python
# _*_ coding:utf-8 _*_

'''

@author: yerik

@contact: xiangzz159@qq.com

@time: 2018/6/22 13:18

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
import urllib
import hashlib
import time
import copy
import operator
from ccxt.base.errors import ExchangeError
from ccxt.base.errors import InvalidOrder
from ccxt.base.errors import OrderNotFound


class coinbig(Exchange):

    def describe(self):
        return self.deep_extend(super(coinbig, self).describe(), {
            'id': 'coinbig',
            'name': 'COINBIG',
            'countries': 'NZ',
            'rateLimit': 2000,
            'userAgent': self.userAgents['chrome39'],
            'version': 'v1',
            'accounts': None,
            'accountsById': None,
            'hostname': 'www.coinbig.com',
            'has': {
                'CORS': False,
                'fetchDepositAddress': False,
                'fetAccountRecords': True,
                'fetchOrderFee': True,
                'fetchOHCLV': True,
                'fetchClosedOrders': False,
                'fetchOrder': True,
                'fetchOrders': False,
                'fetchTradingLimits': True,
                'withdraw': False,
            },
            'timeframes': {
                '1m': '1min',
                '3m': '3min',
                '1h': '1hour',
                '2h': '2hour',
                '1d': '1day',
                '3d': '3day',
                '1w': '1week',
            },
            'urls': {
                'logo': 'https://www.coinbig.com/images/v2/logo.svg',
                'api': 'https://www.coinbig.com',
                'www': 'https://www.coinbig.com/index.html',
                'doc': 'https://github.com/489405826/coinbigapi/wiki/API%E8%AF%B4%E6%98%8E%E6%96%87%E6%A1%A3',
                'fees': 'https://www.coinbig.com/help/ratedescription.html',
            },
            'api': {
                'public': {
                    'get': [
                        'kline',
                        'symbols',
                        'ticker',
                        'depth',
                        'depthList',
                        'price_depth'
                    ],
                },
                'private': {
                    'post': [
                        'order_info',
                        'trades',
                        'userinfoBySymbol',
                        'userinfo',
                        'order_info',
                        'cancel_order',
                        'trade',
                        'batch_trade',
                        'getOrderInfoById'
                    ],
                },
            },
            'fees': {
                'trading': {
                    'tierBased': False,
                    'percentage': True,
                    'maker': 0.002,
                    'taker': 0.002,
                },
            },
        })

    def fetch_markets(self):
        response = self.publicGetSymbols()
        return self.parse_markets(response['data'])

    def parse_markets(self, markets):
        numMarkets = len(markets)
        if numMarkets < 1:
            raise ExchangeError(self.id + ' publicGetCommonSymbols returned empty response: ' + self.json(markets))
        result = []
        for i in range(0, len(markets)):
            market = markets[i]
            qb = market.split('_')
            baseId = qb[0]
            quoteId = qb[1]
            price_decimal = 0
            amount_decimal = 0
            base = baseId.upper()
            quote = quoteId.upper()
            id = baseId + '_' + quoteId
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
                'id': id.lower(),
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

    def fetch_ohlcv(self, symbol, timeframe='3m', since=None, limit=20, params={}):
        self.load_markets()
        market = self.market(symbol)
        request = {
            'symbol': market['id'],
            'type': self.timeframes[timeframe],
            'size': limit,
        }
        if since is not None:
            request['since'] = since
        response = self.publicGetKline(self.extend(request, params))
        return self.parse_ohlcvs(response['data'], market, timeframe, since, limit)

    def parse_ohlcv(self, ohlcv, market=None, timeframe='5m', since=None, limit=None):
        return [
            ohlcv['date'],
            ohlcv['open_price'],
            ohlcv['high'],
            ohlcv['low'],
            ohlcv['close_price'],
            ohlcv['vol']
        ]

    def fetch_ticker(self, symbol, params={}):
        self.load_markets()
        market = self.market(symbol)
        response = self.publicGetTicker(self.extend({
            'symbol': market['id'],
        }, params))
        return self.parse_ticker(response['data'], market)

    def parse_ticker(self, data, market=None):
        symbol = None
        if market:
            symbol = market['symbol']
        timestamp = data['date']
        ticker = data['ticker']
        bid = float(ticker['buy'])
        bidVolume = None
        ask = float(ticker['sell'])
        askVolume = None
        last = None
        high = float(ticker['high'])
        low = float(ticker['low'])
        open = None
        close = None
        change = None
        percentage = None
        average = None
        baseVolume = None
        quoteVolume = float(ticker['vol'])
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

    def create_order(self, symbol, type, side, amount, price=None, params={}):
        self.load_markets()
        market = self.market(symbol)
        order = {
            'amount': self.amount_to_precision(symbol, amount),
            'symbol': market['id'],
            'type': side + '_' + type,
            'price': price,
        }
        if type == 'limit':
            order['price'] = self.price_to_precision(symbol, price)
        response = self.privatePostTrade(self.extend(order, params))
        return {
            'info': response,
            'id': response['order_id'],
        }

    def cancel_order(self, id, symbol=None, params={}):
        return self.privatePostCancel_order({'order_id': id})


    def fetch_order_book(self, symbol, limit=200, params={}):
        self.load_markets()
        market = self.market(symbol)
        response = self.publicGetDepth(self.extend({
            'symbol': market['id'],
            'size': limit,
        }, params))
        order_book = response['data']
        ts = str(int(time.time() * 1000))
        return self.parse_order_book(order_book, ts)


    def fetch_order(self, id, symbol=None, params={}):
        self.load_markets()
        market = self.market(symbol)
        response = self.privatePostGetOrderInfoById(self.extend({
            'order_id': id,
        }, params))
        return self.parse_order(response['data'], market)

    def parse_order(self, order, market=None):
        side = self.get_side(int(order['entrustType']))
        type = self.get_limit(int(order['isLimit']))
        status = self.parse_order_status(order['state'])
        symbol = None
        if not market:
            if 'symbol' in order:
                if order['symbol'] in self.markets_by_id:
                    marketId = order['symbol']
                    market = self.markets_by_id[marketId]
        if market:
            symbol = market['symbol']
        timestamp = order['created_date']
        amount = float(order['amount'])
        filled = float(order['amount']) - float(order['leftCount'])
        remaining = float(order['leftCount'])
        price = float(order['price'])
        cost = float(order['avg_price']) * filled
        fee = 0
        average = float(order['avg_price'])
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

    def get_side(self, sideType):
        if sideType == 0:
            return 'buy'
        elif sideType == 1:
            return 'sell'
        else:
            return sideType

    def get_limit(self, isLimit):
        if isLimit == 0:
            return 'limit'
        elif isLimit == 1:
            return 'market'
        else:
            return isLimit

    # 未确定
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

    def fetch_balance(self, params={}):
        self.load_markets()
        response = self.privatePostUserinfo(params)
        result = {'info': response}
        balances = response['balances']
        for i in range(0, len(balances)):
            balance = balances[i]
            currency = balance['asset']
            if currency in self.currencies_by_id:
                currency = self.currencies_by_id[currency]['code']
            account = {
                'free': float(balance['free']),
                'used': float(balance['locked']),
                'total': 0.0,
            }
            account['total'] = self.sum(account['free'], account['used'])
            result[currency] = account
        return self.parse_balance(result)


    def sign(self, path, api='public', method='GET', params={}, headers=None, body=None):
        url = '/api/publics/' + self.version + '/' + self.implode_params(path, params)
        query = self.omit(params, self.extract_params(path))
        if api == 'private':
            self.check_required_credentials()
            params['apikey'] = self.apiKey
            _params = copy.copy(params)
            sort_params = sorted(_params.items(), key=operator.itemgetter(0))
            sort_params = dict(sort_params)
            sort_params['secret_key'] = self.secret
            string = urllib.parse.urlencode(sort_params)
            _sign = hashlib.md5(bytes(string.encode('utf-8'))).hexdigest().upper()
            params['sign'] = _sign
        else:
            if params:
                url += '?' + self.urlencode(params)
        url = self.urls['api'] + url
        return {'url': url, 'method': method, 'body': body, 'headers': headers}


if __name__ == '__main__':
    ex = coinbig({
        'apiKey': 'EDDBFC562C1A42774FBF2CF2DAB3CE30',
        'secret': 'E73CA6A88E7CF276B5D36076A974A8C0'
    })
    # print(ex.fetch_ohlcv('BTC/USDT'))
    print(ex.create_order('BTC/USDT', 'limit', 'buy', 1.0, 6780))
