import configparser
import threading
import time
import requests

from dingdong_api import DingDongApi
from cache import Cache
from logger import log


class CheckHomeFlowThread(threading.Thread):
    config = None
    api = None
    start_up_flag = True
    cache = None

    def __init__(self, config_name):
        super().__init__(name=config_name)

        self.config_name = config_name

        self.config = configparser.ConfigParser()
        self.config.read(self.config_name, encoding='utf-8')
        self.api = DingDongApi(self.config)
        self.cache = Cache(5 * 60)

    def run(self):
        while True:
            self.check_flow()
            time.sleep(5)

    def check_flow(self):
        product_list = self.api.get_home_flow_detail()

        if product_list:
            product_list = list(filter(lambda item: self.cache.get(item['id']) is None, product_list))
            for product in product_list:
                if not self.start_up_flag:
                    bark_id_list = self.config.get('notify', 'bark_id_list').split(',')
                    for bark_id in bark_id_list:
                        log().info("有商品上架了: %s" % (product['name']))
                        requests.get(
                            'https://api.day.app/%s/商品上架监控/有商品上架了:%s?group=上架监控&level=timeSensitive'
                            % (bark_id, product['name']))
                self.cache.merge(product['id'])
        self.start_up_flag = False

