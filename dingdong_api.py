import requests
import json
import time
from logger import log


class DingDongApi(object):
    HEADERS = {
        "referer": "https://servicewechat.com/wx1e113254eda17715/422/page-frame.html",
        "ddmc-city-number": "0101",
        "ddmc-app-client-id": "4",
        "ddmc-api-version": "9.49.2",
        "ddmc-os-version": "[object Undefined]",
        "ddmc-build-version": "9.49.2",
        "ddmc-channel": "applet",
        "ddmc-ip": "",
        "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) "
                      "Mobile/15E148 MicroMessenger/8.0.18(0x1800123c) NetType/WIFI Language/zh_CN "
    }

    DATA = {
        "app_version": "2.82.0",
        "h5_source": "",
        "channel": "applet",
        "api_version": "9.49.2",
        "applet_source": "",
        "city_number": "0101",
        "sharer_uid": "",
        "device_token": "WHJMrwNw1k/FKPjcOOgRd+BL63ErIKsK/eLG0mUpGJZ16P9zFvfu/F1156njLyfZ/niKqWLb3XJOvdNnwNvkiTw2b6U7pE/0ddCW1tldyDzmauSxIJm5Txg==1487582755342",
        "longitude": "121.489999",
        "app_client_id": "4"
    }

    def __init__(self, config):
        self.HEADERS['station-id'] = config.get('user', 'station-id')
        self.HEADERS['ddmc-longitude'] = config.get('user', 'longitude')
        self.HEADERS['ddmc-latitude'] = config.get('user', 'latitude')
        self.HEADERS['ddmc-device-id'] = config.get('user', 'openid')

        self.DATA['station_id'] = config.get('user', 'station-id')
        self.DATA['longitude'] = config.get('user', 'longitude')
        self.DATA['latitude'] = config.get('user', 'latitude')
        self.DATA['openid'] = config.get('user', 'openid')

    @staticmethod
    def is_success(resp):
        if 0 != resp['code']:
            if '405' == resp['code']:
                log().error(
                    "失败, 出现此问题有三个可能 1.偶发，无需处理 2.一个账号一天只能下两单  "
                    "3.不要长时间运行程序，目前已知有人被风控了，暂时未确认风控的因素是ip还是用户或设备相关信息，如果要测试用单次执行模式，并发只能用于6点、8点半的前一分钟，然后执行时间不能超过2"
                    "分钟，如果买不到就不要再执行程序了，切忌切忌，如果已经被风控的可以尝试过一段时间再试，或者换号")
            else:
                log().error("失败,服务器返回无法解析的内容:" + json.dumps(resp, indent=2, ensure_ascii=False))
            return False
        if resp['success']:
            return True
        if "您的访问已过期" == resp['message']:
            log().info("用户信息失效，请确保UserConfig参数准确，并且微信上的叮咚小程序不能退出登录")
            return False

    # 获取商品库存
    def get_product_detail(self, id):
        param = self.DATA
        param['id'] = id
        resp = requests.get('https://maicai.api.ddxq.mobi/guide-service/productApi/productDetail/info',
                            params=param,
                            headers=self.HEADERS).json()

        if not self.is_success(resp):
            return None

        product_detail = resp['data']['detail']
        server_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(resp['server_time']))
        return {"server_time": server_time, "name": product_detail['product_name'],
                "stock": product_detail['stock_number'],
                'unit': product_detail['sale_unit'], 'id': product_detail['id']}

    # 搜索商品
    def search_product(self, keyword):
        param = self.DATA
        param['keyword'] = keyword
        resp = requests.get('https://maicai.api.ddxq.mobi/search/searchProduct', params=param,
                            headers=self.HEADERS).json()

        if not self.is_success(resp):
            return None

        result = []
        product_list = resp['data']['product_list']
        for product in product_list:
            result.append({'id': product['id'], 'name': product['name'], 'price': product['price'],
                           'stock': product['stock_number'], 'unit': product['sale_unit']})

        return result

    # 添加到购物车
    def add_cart(self, config, product_id, buy_num=1):
        param = self.DATA
        headers = self.HEADERS
        param['uid'] = config.get('user', 'uid')
        param['products'] = '[{"id":"%s","count":%d,"activity_id":"","vip_activity_id":"",' \
                            '"mandatory_check":"1","mandatory_count":0,"batch_type":-1,"algo_info":{},"sizes":[]}] ' \
                            % (product_id, buy_num)

        headers['ddmc-uid'] = config.get('user', 'uid')
        headers['cookie'] = config.get('user', 'cookie')

        resp = requests.post('https://maicai.api.ddxq.mobi/cart/add', params=param, headers=headers).json()

        if not self.is_success(resp):
            return None

    def get_cart(self, config):
        param = self.DATA
        headers = self.HEADERS

        param['uid'] = config.get('user', 'uid')
        param['is_load'] = '1'
        headers['ddmc-uid'] = config.get('user', 'uid')
        headers['cookie'] = config.get('user', 'cookie')

        resp = requests.get('https://maicai.api.ddxq.mobi/cart/index', params=param, headers=headers).json()
        if not self.is_success(resp):
            return None

        if len(resp['data']['new_order_product_list']) == 0:
            log().info("购物车可选商品为空")
            return None
        new_order_product = resp['data']['new_order_product_list'][0]
        products = new_order_product['products']

        return {
            'products': products,
            'parent_order_sign': resp['data']['parent_order_info']['parent_order_sign'],
            'total_money': new_order_product['total_money'],
            'total_origin_money': new_order_product['total_origin_money'],
            'goods_real_money': new_order_product['goods_real_money'],
            'total_count': new_order_product['total_count'],
            'cart_count': new_order_product['cart_count'],
            'is_presale': new_order_product['is_presale'],
            'instant_rebate_money': new_order_product['instant_rebate_money'],
            'used_balance_money': new_order_product['used_balance_money'],
            'can_used_balance_money': new_order_product['can_used_balance_money'],
            'used_point_num': new_order_product['used_point_num'],
            'used_point_money': new_order_product['used_point_money'],
            'can_used_point_num': new_order_product['can_used_point_num'],
            'can_used_point_money': new_order_product['can_used_point_money'],
            'is_share_station': new_order_product['is_share_station'],
            'only_today_products': new_order_product['only_today_products'],
            'only_tomorrow_products': new_order_product['only_tomorrow_products'],
            'package_type': new_order_product['package_type'],
            'package_id': new_order_product['package_id'],
            'front_package_text': new_order_product['front_package_text'],
            'front_package_type': new_order_product['front_package_type'],
            'front_package_stock_color': new_order_product['front_package_stock_color'],
            'front_package_bg_color': new_order_product['front_package_bg_color']
        }

    def categories_new_detail(self, config, category_id):
        param = self.DATA
        headers = self.HEADERS

        param['category_id'] = category_id
        param['uid'] = config.get('user', 'uid')

        resp = requests.get('https://maicai.api.ddxq.mobi/homeApi/categoriesNewDetail', params=param,
                            headers=headers).json()

        if not self.is_success(resp):
            return None

        product_list = []
        in_stock_product = list(filter(lambda product: product['stock_number'] > 0, resp['data']['products']))
        for product in in_stock_product:
            product_list.append({'id': product['id'], 'name': product['name'], 'price': product['price'],
                                 'stock_number': product['stock_number']})

        return product_list

    def get_multi_reserve_time(self, address_id, cart_info):
        param = self.DATA
        headers = self.HEADERS

        param['addressId'] = address_id
        param['products'] = '[' + json.dumps(cart_info.get('products'), ensure_ascii=False) + ']'
        param['isBridge'] = 'false'

        resp = requests.post('https://maicai.api.ddxq.mobi/order/getMultiReserveTime', params=param,
                             headers=headers).json()
        if not self.is_success(resp):
            return None

        time_list = resp['data'][0]['time'][0]['times']
        for time in time_list:
            if time['disableType'] == 0:
                return {'reserved_time_start': time['start_timestamp'],
                        'reserved_time_end': time['end_timestamp']
                        }

    # 获取下单参数
    def check_order(self, config, address_id, cart_info, reserve_time):
        param = self.DATA
        headers = self.HEADERS

        del param['products']

        param['address_id'] = address_id
        param['user_ticket_id'] = 'default'
        param['freight_ticket_id'] = 'default'
        param['is_use_point'] = '0'
        param['is_use_balance'] = '0'
        param['is_buy_vip'] = '0'
        param['coupons_id'] = ''
        param['is_buy_coupons'] = '0'
        param['check_order_type'] = '0'
        param['is_support_merge_payment'] = '1'
        param['showData'] = 'true'
        param['showMsg'] = 'false'
        param['packages'] = json.dumps([{
            'products': cart_info['products'],
            'total_money': cart_info['total_money'],
            'total_origin_money': cart_info['total_origin_money'],
            'goods_real_money': cart_info['goods_real_money'],
            'total_count': cart_info['total_count'],
            'cart_count': cart_info['cart_count'],
            'is_presale': cart_info['is_presale'],
            'instant_rebate_money': cart_info['instant_rebate_money'],
            'used_balance_money': cart_info['used_balance_money'],
            'can_used_balance_money': cart_info['can_used_balance_money'],
            'used_point_num': cart_info['used_point_num'],
            'used_point_money': cart_info['used_point_money'],
            'can_used_point_num': cart_info['can_used_point_num'],
            'can_used_point_money': cart_info['can_used_point_money'],
            'is_share_station': cart_info['is_share_station'],
            'only_today_products': cart_info['only_today_products'],
            'only_tomorrow_products': cart_info['only_tomorrow_products'],
            'package_type': cart_info['package_type'],
            'package_id': cart_info['package_id'],
            'front_package_text': cart_info['front_package_text'],
            'front_package_type': cart_info['front_package_type'],
            'front_package_stock_color': cart_info['front_package_stock_color'],
            'front_package_bg_color': cart_info['front_package_bg_color'],
            'reserved_time': {
                'reserved_time_start': reserve_time['reserved_time_start'],
                'reserved_time_end': reserve_time['reserved_time_end']
            }
        }], ensure_ascii=False)

        log().info(param)
        resp = requests.post('https://maicai.api.ddxq.mobi/order/checkOrder', params=param, headers=headers).json()
        if not self.is_success(resp):
            return None

        return resp

    def get_home_flow_detail(self):
        param = self.DATA
        param['tab_type'] = 1
        param['page'] = 1
        headers = self.HEADERS
        resp = requests.get('https://maicai.api.ddxq.mobi/homeApi/homeFlowDetail', params=param,
                            headers=headers).json()
        if not self.is_success(resp):
            return None

        product_list = resp['data']['list']
        result = []
        for product in product_list:
            result.append({'id': product['id'], 'name': product['name']})
        return result
