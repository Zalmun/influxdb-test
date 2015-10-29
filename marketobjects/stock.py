import urllib2
import json
import logging
from datetime import date

from utils import return_as_number, byteify, fix_output

logger = logging.getLogger(__name__)


class StockOptionPosition:
    def __init__(self, symbol, position_type, ask, bid, change, cid, change_dir, expiry_date,
                 open_interest, price, option_code, strike, volume):
        self.symbol = symbol
        self.positionType = position_type
        self.ask = return_as_number(ask)
        self.bid = return_as_number(bid)
        self.change = change
        self.cid = cid
        self.changeDir = change_dir
        self.expiryDate = expiry_date
        self.openInterest = open_interest
        self.price = return_as_number(price)
        self.optionCode = option_code
        self.strike = return_as_number(strike)
        self.volume = int(return_as_number(volume))

    def get_symbol(self):
        return self.symbol

    def get_type(self):
        return self.positionType

    def get_ask(self):
        return self.ask

    def get_bid(self):
        return self.bid

    def get_expiry_date(self):
        return self.expiryDate

    def get_expiry_date_formatted(self):
        return self.expiryDate.strftime('%Y-%m-%d')

    def get_price(self):
        return self.price

    def get_option_code(self):
        return self.optionCode

    def get_strike_price(self):
        return self.strike

    def get_volume(self):
        return self.volume


class StockOption:
    def __init__(self, parent, day, month, year):
        self.parent_stock = parent
        self.expiryDay = int(day)
        self.expiryMonth = int(month)
        self.expiryYear = int(year)
        self.expiryDate = date(self.expiryYear, self.expiryMonth, self.expiryDay)
        self.calls = []
        self.puts = []

    def get_date(self):
        return self.expiryDate

    def get_date_formatted(self):
        return self.expiryDate.strftime('%Y-%m-%d %H:%M:%S.000')

    def get_symbol(self):
        return self.parent.get_symbol()

    def download_prices(self):
        url = "http://www.google.com/finance/option_chain?q=%s&expd=%d&expm=%d&expy=%d&output=json" % \
              (self.parent.get_symbol_for_url(), self.expiryDay, self.expiryMonth, self.expiryYear)
        raw_data = fix_output(urllib2.urlopen(url).read())
        option_data = byteify(json.loads(raw_data))
        self.calls = self._get_prices('call', option_data)
        self.puts = self._get_prices('put', option_data)

    def _get_prices(self, position_type, option_data):
        positions = []
        for option in option_data[position_type + 's']:
            if 'cs' not in option:
                change_dir = 'unknown'
            else:
                change_dir = option['cs']
            positions.append(StockOptionPosition(self.get_symbol(), position_type, option['a'], option['b'],
                                                 option['c'], option['cid'], change_dir, self.expiryDate, option['oi'],
                                                 option['p'], option['s'], option['strike'], option['vol']))
        return positions

    def get_calls_count(self):
        return len(self.calls)

    def get_puts_count(self):
        return len(self.puts)

    def get_calls(self):
        return self.calls

    def get_puts(self):
        return self.puts


class Stock:
    MARKETS = ['', 'NYSE']

    def __init__(self, symbol):
        self.symbol = symbol
        self.symbol_for_url = None
        self.options = []
        self.price = 0.00

        option_dates = self.__download_expiry_dates()
        if option_dates is not None:
            for expiry in option_dates['expirations']:
                self.options.append(StockOption(self, expiry['d'], expiry['m'], expiry['y']))

            if 'underlying_price' in option_dates:
                self.price = return_as_number(option_dates['underlying_price'])

            for option in self.options:
                option.download_prices()

    def get_symbol(self):
        return self.symbol

    def get_symbol_for_url(self):
        if self.symbol_for_url is not None:
            return self.symbol_for_url
        else:
            return self.symbol

    def get_options(self):
        return self.options

    def get_price(self):
        return self.price

    def __download_expiry_dates(self):
        option_dates = None
        base_url = "http://www.google.com/finance/option_chain?q=%s&output=json"
        for market in self.MARKETS:
            adjusted_symbol = self.symbol
            if len(market) > 0:
                # add the market as a prefix separated by a colon;  ex. 'NYSE:V'
                adjusted_symbol = '%s%%3A%s' % (market, self.symbol)

            url = base_url % adjusted_symbol
            logger.info('Attempting to get expiry dates for [%s] with URL: [%s]' % (self.symbol, url))
            raw_data = fix_output(urllib2.urlopen(url).read())
            option_dates = byteify(json.loads(raw_data))

            if 'expirations' in option_dates:
                self.symbol_for_url = adjusted_symbol
                break

            logger.info('No expiry dates found for symbol [%s] with market [%s]' % (self.symbol, market))
            option_dates = None

        return option_dates
