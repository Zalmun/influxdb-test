import logging
import logging.handlers
from influxdb import InfluxDBClient
from marketobjects import Stock, process_stock_list

STOCKS = [
    'AAPL',
    'FB',
    'V',
    'MSFT',
    'TWTR',
    'VRX',
    'TSLA',
]

LOG_FILENAME = 'options_downloader_influxdb.log'

logger = logging.getLogger()


def setup_logging():
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)

    fh = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=10000000, backupCount=3)
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)


def make_stock_objects():
    all_stocks = list()
    for symbol in STOCKS:
        new_stock = Stock(symbol)
        if len(new_stock.get_options()) > 0:
            all_stocks.append(new_stock)

    return all_stocks


def main():
    setup_logging()
    client = InfluxDBClient(database='testmarket')
    logger.log("Downloading stock prices and options")
    all_stocks = make_stock_objects()
    process_stock_list(client, all_stocks)

if __name__ == "__main__" :
    main()
