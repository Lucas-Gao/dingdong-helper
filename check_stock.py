import random

import requests
import time
import configparser

from logger import log
from cache import Cache

from fetch_stock import FetchStockThread

from dingdong_api import DingDongApi


def check_product_in_cart(in_stock_product_list):
    try:
        cart_info = api.get_cart(config)
        if cart_info:
            product_list_in_cart = list(map(lambda product: product['id'], cart_info.get('products')))
            # 不在购物车中的商品
            need_to_add_cart = list(filter(lambda item: item not in product_list_in_cart,
                                           list(map(lambda product: product['id'], in_stock_product_list))))
            # 添加到购物车
            if need_to_add_cart:
                for product_id in need_to_add_cart:
                    log().info("正在将商品加入到购物车.. 商品id: %s", product_id)
                    api.add_cart(config, product_id)
        else:
            for product in in_stock_product_list:
                log().info("正在将商品加入到购物车.. 商品id: %s", product['id'])
                api.add_cart(config, product['id'])
    except Exception as e:
        print(e)
        return None


def search_in_stock_product(key_word):
    product_list = api.search_product(key_word)
    if product_list:
        in_stock_product_list = list(
            filter(lambda product: product['stock'] > 0 and product['id'] not in block_product_list,
                   product_list))

        return in_stock_product_list
    return []


if __name__ == '__main__':

    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    api = DingDongApi(config)

    FetchStockThread(api).start()
    while True:
        if time.strptime(time.ctime()).tm_hour not in list(range(6, 20)):
            time.sleep(60)
            continue
        else:
            config = configparser.ConfigParser()
            config.read('config.ini', encoding='utf-8')
            try:
                block_product_list = config.get('search', 'block_product_list').split(',')
                bark_id_list = config.get('notify', 'bark_id_list').split(',')
                # 搜索商品

                for key_word in config.get('search', 'search_key').split(','):
                    in_stock_product_list = search_in_stock_product(key_word)
                    # 如果有库存, 则通知
                    if (len(in_stock_product_list)) > 0:
                        check_product_in_cart(in_stock_product_list)
                        for item in in_stock_product_list:
                            log().info("%s有库存了: %s, product_id: %s", key_word, item['name'], item['id'])

                            cache = Cache.instance()
                            count = cache.merge(item['id'])
                            if count <= 3:
                                for bark_id in bark_id_list:
                                    requests.get('https://api.day.app/%s/库存监控/关注的'
                                                 '[%s]有库存了?group=库存监控&level=timeSensitive' % (bark_id, key_word))

                        time.sleep(random.randint(1, 10))
                    else:
                        log().info("%s暂无库存", key_word)
            except:
                print('exception on search product')
            time.sleep(5)
