import logging
from influxdb import SeriesHelper
from influxdb.exceptions import InfluxDBClientError

logger = logging.getLogger(__name__)


def process_stock_list(client, stocks):
    for stock in stocks:
        logger.info("%s: current price = %s" % (stock.get_symbol(), stock.get_price()))
        StockSeries(stock_symbol=stock.get_symbol(), price=stock.get_price())
        options = stock.get_options()
        for option in options:
            logger.info("%s: %s - # calls: %s, # puts: %s" % (stock.get_symbol(), option.get_date_formatted(),
                                                              option.get_calls_count(), option.get_puts_count()))
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
        logger.log("Writing to InfluxDB")
        StockSeries.commit(client)
        OptionSeries.commit(client)
        logger.log("Done")
    except InfluxDBClientError:
        logger.error(StockSeries._json_body_())
        logger.error(OptionSeries._json_body_())
        raise


class StockSeries(SeriesHelper):
    class Meta:
        series_name = 'stock.{stock_symbol}'
        fields = ['price']
        tags = ['stock_symbol']


class OptionSeries(SeriesHelper):
    class Meta:
        series_name = 'stock.{stock_symbol}.{option_type}'
        fields = ['ask', 'bid', 'price', 'volume']
        tags = ['stock_symbol', 'option_id', 'expiry_date', 'strike', 'option_type']