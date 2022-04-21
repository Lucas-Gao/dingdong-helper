import time
import threading

from logger import log


class ClearCountThread(threading.Thread):
    cache = None
    sleep_time = 30 * 60

    def __init__(self, cache, sleep_time):
        super().__init__()
        self.cache = cache
        if sleep_time:
            self.sleep_time = sleep_time

    def run(self):
        while True:
            time.sleep(self.sleep_time)
            log().info("正在清理缓存..当前缓存中的对象: %s" % (self.cache.get_all_key()))
            self.cache.clear()


class Cache(object):
    __in_stock_product_dist = {}

    def __init__(self, sleep_time=30*60):
        log().info("缓存清理线程已启动..")
        ClearCountThread(self, sleep_time=sleep_time).start()

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
