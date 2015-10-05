import urllib2
import json
import re
from datetime import date

import pprint


class StockOptionPosition:
    def __init__(self, symbol, position_type, ask, bid, change, cid, change_dir, expiry_date,
                 open_interest, price, option_code, strike, volume):
        self.symbol = symbol
        self.positionType = position_type
        self.ask = ask
        self.bid = bid
        self.change = change
        self.cid = cid
        self.changeDir = change_dir
        self.expiryDate = expiry_date
        self.openInterest = open_interest
        self.price = price
        self.optionCode = option_code
        self.strike = strike
        self.volume = volume


class StockOption:
    def __init__(self, symbol, day, month, year):
        self.symbol = symbol
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
        return self.symbol

    def download_prices(self):
        url = "http://www.google.com/finance/option_chain?q=%s&expd=%d&expm=%d&expy=%d&output=json" % \
              (self.symbol, self.expiryDay, self.expiryMonth, self.expiryYear)
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
            positions.append(StockOptionPosition(self.symbol, position_type, option['a'], option['b'], option['c'],
                                                 option['cid'], change_dir, self.expiryDate, option['oi'],
                                                 option['p'], option['s'], option['strike'], option['vol']))
        return positions

    def get_calls_count(self):
        return len(self.calls)

    def get_puts_count(self):
        return len(self.puts)


def fix_output(json_to_fix):
    first_pass = re.sub('(\w+:)(\d+\.?\d*)', r'\1"\2"', json_to_fix)
    second_pass = re.sub('(\w+):', r'"\1":', first_pass)
    return second_pass


def byteify(input_str):
    if isinstance(input_str, dict):
        return {byteify(key): byteify(value) for key, value in input_str.iteritems()}
    elif isinstance(input_str, list):
        return [byteify(element) for element in input_str]
    elif isinstance(input_str, unicode):
        return input_str.encode('utf-8')
    else:
        return input_str


def get_option_expiry_dates(symbol):
    url = "http://www.google.com/finance/option_chain?q=%s&output=json" % symbol
    raw_data = fix_output(urllib2.urlopen(url).read())
    option_dates = byteify(json.loads(raw_data))

    options = []
    for expiry in option_dates['expirations']:
        options.append(StockOption(symbol, expiry['d'], expiry['m'], expiry['y']))

    return options


def main():
    all_options = dict()
    all_options['AAPL'] = []

    for symbol in all_options:
        all_options[symbol] = get_option_expiry_dates(symbol)
        for option in all_options[symbol]:
            print "Downloading prices for %s, expiry %s" % (symbol, option.get_date())
            option.download_prices()

    for symbol, options in all_options.iteritems():
        for option in options:
            print "%s: %s - # calls: %s, # puts: %s" % (symbol, option.get_date_formatted(),
                                                        option.get_calls_count(), option.get_puts_count())


if __name__ == "__main__" :
    main()