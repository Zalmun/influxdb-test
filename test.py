import urllib2
import json
import re
from datetime import date

from influxdb import SeriesHelper
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError


myClient = InfluxDBClient(database='testmarket')


def byteify(input_str):
    if isinstance(input_str, dict):
        return {byteify(key): byteify(value) for key, value in input_str.iteritems()}
    elif isinstance(input_str, list):
        return [byteify(element) for element in input_str]
    elif isinstance(input_str, unicode):
        return input_str.encode('utf-8')
    else:
        return input_str


def fix_output(json_to_fix):
    first_pass = re.sub('(\w+:)(\d+\.?\d*)', r'\1"\2"', json_to_fix)
    second_pass = re.sub('(\w+):', r'"\1":', first_pass)
    return second_pass


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def return_as_number(s):
    if is_number(s):
        return float(s)
    else:
        return 0.00


class StockSeries(SeriesHelper):
    class Meta:
        client = myClient
        series_name = 'stock.{stock_symbol}'
        fields = ['price']
        tags = ['stock_symbol']


class OptionSeries(SeriesHelper):
    class Meta:
        client = myClient
        series_name = 'stock.{stock_symbol}.{option_type}'
        fields = ['ask', 'bid', 'price', 'volume']
        tags = ['stock_symbol', 'option_id', 'expiry_date', 'strike', 'option_type']


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

    def get_calls(self):
        return self.calls

    def get_puts(self):
        return self.puts


class Stock:
    def __init__(self, symbol):
        self.symbol = symbol
        self.options = []
        self.price = 0.00

        url = "http://www.google.com/finance/option_chain?q=%s&output=json" % symbol
        raw_data = fix_output(urllib2.urlopen(url).read())
        option_dates = byteify(json.loads(raw_data))

        for expiry in option_dates['expirations']:
            self.options.append(StockOption(self.symbol, expiry['d'], expiry['m'], expiry['y']))

        if 'underlying_price' in option_dates:
            self.price = return_as_number(option_dates['underlying_price'])

        for option in self.options:
            option.download_prices()

    def get_symbol(self):
        return self.symbol

    def get_options(self):
        return self.options

    def get_price(self):
        return self.price


def main():
    print "Downloading stock prices and options..."
    all_stocks = list()
    all_stocks.append(Stock('AAPL'))
    all_stocks.append(Stock('FB'))
    all_stocks.append(Stock('V'))
    all_stocks.append(Stock('MSFT'))
    all_stocks.append(Stock('TWTR'))
    all_stocks.append(Stock('VXT'))
    all_stocks.append(Stock('TSLA'))

    for stock in all_stocks:
        print "%s: current price = %s" % (stock.get_symbol(), stock.get_price())
        StockSeries(stock_symbol=stock.get_symbol(), price=stock.get_price())
        options = stock.get_options()
        for option in options:
            print "%s: %s - # calls: %s, # puts: %s" % (stock.get_symbol(), option.get_date_formatted(),
                                                        option.get_calls_count(), option.get_puts_count())
            option_calls = option.get_calls()
            for option_call in option_calls:
                OptionSeries(stock_symbol=option_call.get_symbol(), option_type=option_call.get_type(),
                             option_id=option_call.get_option_code(), expiry_date=option_call.get_expiry_date_formatted(),
                             strike=option_call.get_strike_price(), ask=option_call.get_ask(), bid=option_call.get_bid(),
                             price=option_call.get_price(), volume=option_call.get_volume())

            option_puts = option.get_puts()
            for option_put in option_puts:
                OptionSeries(stock_symbol=option_put.get_symbol(), option_type=option_put.get_type(),
                             option_id=option_put.get_option_code(), expiry_date=option_put.get_expiry_date_formatted(),
                             strike=option_put.get_strike_price(), ask=option_put.get_ask(), bid=option_put.get_bid(),
                             price=option_put.get_price(), volume=option_put.get_volume())

    try:
        print "Writing to InfluxDB"
        StockSeries.commit()
        OptionSeries.commit()
        print "Done"
    except InfluxDBClientError:
        print StockSeries._json_body_()
        print OptionSeries._json_body_()
        raise

if __name__ == "__main__" :
    main()
