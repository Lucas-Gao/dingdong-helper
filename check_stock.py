import random
import threading

import requests
import time
import configparser

from logger import log
from cache import Cache

from dingdong_api import DingDongApi


class CheckStockThread(threading.Thread):
    config_name = None
    config = None
    api = None
    cache = None

    def __init__(self, config_name):
        super().__init__(name=config_name)
        self.config_name = config_name
        self.cache = Cache()

    def check_product_in_cart(self, in_stock_product_list):
        cart_info = None
        while cart_info is None:
            cart_info = self.api.get_cart(self.config)

        # 购物车中存在可下单的商品
        if cart_info:
            product_list_in_cart = list(map(lambda item: item['id'], cart_info.get('products')))
            # 只将不存在购物车中的商品进行加购
            for in_stock_product in in_stock_product_list[:]:
                if in_stock_product['id'] in product_list_in_cart:
                    in_stock_product_list.remove(in_stock_product)

        # 添加到购物车
        if in_stock_product_list:
            for product in in_stock_product_list[:]:
                log().info("正在将商品加入到购物车.. 商品id: %s, 商品名称: %s", product['id'], product['name'])
                success_to_cart = self.api.add_cart(self.config, product['id'],
                                                    2 if product['buy_limit'] == 0 else min(2, product['buy_limit']))

                if not success_to_cart:
                    in_stock_product_list.remove(product)
        return in_stock_product_list

    def search_in_stock_product(self, key_word):

        block_product_id_list = self.config.get('search', 'block_product_id_list').split(',')
        block_product_name_list = self.config.get('search', 'block_product_name_list').split(',')

        product_list = self.api.search_product(key_word)
        if product_list:
            in_stock_product_list = []
            for product in product_list:
                if product['stock'] > 0 and product['id'] not in block_product_id_list:
                    not_block_product = True
                    for block_name in block_product_name_list:
                        if product['name'].find(block_name) != -1:
                            not_block_product = False
                    if not_block_product:
                        in_stock_product_list.append(product)
            return in_stock_product_list
        return []

    def run(self):
        while True:
            if time.strptime(time.ctime()).tm_hour not in list(range(6, 22)):
                time.sleep(60)
                continue
            else:
                self.config = configparser.ConfigParser()
                self.config.read(self.config_name, encoding='utf-8')
                self.api = DingDongApi(self.config)
                try:
                    bark_id_list = self.config.get('notify', 'bark_id_list').split(',')

                    # 搜索商品
                    for key_word in self.config.get('search', 'search_key').split(','):
                        in_stock_product_list = self.search_in_stock_product(key_word)
                        # 如果有库存, 则通知
                        if in_stock_product_list:
                            in_stock_product_list = self.check_product_in_cart(in_stock_product_list)
                            for item in in_stock_product_list:
                                log().info("%s有库存了: 商品名称: %s, 单价: %s, product_id: %s", key_word, item['name'],
                                           item['price'], item['id'])

                                if self.cache.merge(item['id']) == 1:
                                    for bark_id in bark_id_list:
                                        requests.get(
                                            'https://api.day.app/%s/库存监控/关注的[%s]有库存了:%s,单价:%s?group=库存监控&level=timeSensitive'
                                            % (bark_id, key_word, item['name'], item['price']))

                            time.sleep(random.randint(1, 10))
                        else:
                            log().info("%s暂无库存", key_word)
                except:
                    print('exception on search product')
                time.sleep(5)
