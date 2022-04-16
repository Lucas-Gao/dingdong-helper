import time
import threading

from logger import log


class ClearCountThread(threading.Thread):
    def run(self):
        while True:
            time.sleep(30 * 60)
            log().info("正在清理缓存..")
            Cache.instance().clear()


class Cache(object):
    __in_stock_product_dist = {}

    def __init__(self):
        log().info("缓存清理已启动")
        ClearCountThread().start()

    def merge(self, product_id):
        count = 1
        if self.__in_stock_product_dist.get(product_id) is None:
            self.__in_stock_product_dist[product_id] = count
        else:
            count = self.__in_stock_product_dist.get(product_id) + 1
            self.__in_stock_product_dist[product_id] = count
        return count

    def get_all_key(self):
        return self.__in_stock_product_dist.keys()

    def get(self, product_id):
        return self.__in_stock_product_dist.get(product_id)

    def clear(self):
        self.__in_stock_product_dist.clear()

    @classmethod
    def instance(cls):
        if not hasattr(cls, 'ins'):
            instance_obj = cls()
            setattr(cls, 'ins', instance_obj)
        return getattr(cls, 'ins')
