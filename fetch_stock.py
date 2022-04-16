import configparser
import time
from prometheus_client import start_http_server, CollectorRegistry, Gauge

from cache import Cache
from dingdong_api import DingDongApi

from logger import log
import threading

reg = CollectorRegistry()
gauge = Gauge(
    'monitor', '库存监控',
    ['name', 'id'], registry=reg
)


class FetchStockThread(threading.Thread):
    api = None

    def __init__(self, api):
        super().__init__()
        self.api = api

    def process_request(self):
        try:
            cache = Cache.instance()
            product_list = cache.get_all_key()
            if product_list:
                for product_id in product_list:
                    detail = self.api.get_product_detail(product_id)
                    if detail:
                        # gauge.labels(name=detail["name"], server_time=detail['server_time']).set(detail["stock"])
                        gauge.labels(name=detail["name"], id=detail['id']).set(detail["stock"])
        except Exception as e:
            log().info("error", e)
        time.sleep(5)

    def run(self):
        start_http_server(8000, registry=reg)
        while True:
            self.process_request()


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    api = DingDongApi(config)

    FetchStockThread(api).start()
