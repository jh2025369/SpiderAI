import execjs
import requests
import json
import os

script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(script_path)
js_path = os.path.join(script_dir, "miaoshou.js")

cookie = ''

def loginParam(mobile, password):
    with open(js_path, 'r') as file:
        js_code = file.read()
        try:
            ctx = execjs.compile(js_code)
            result = ctx.call("loginParam", mobile, password)
            print(result)
            return result
        except Exception as e:
            print(f"Error executing JavaScript code: {e}")


def login(username=None, password=None):
    global cookie
    url = "https://erp.91miaoshou.com/api/auth/account/login"
    data = loginParam(username, password)
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'X-BreadCrumb': 'system-login'
    }
    try:
        response = requests.post(url, data=data, headers=headers)
        res = json.loads(response.text)
        cookies = response.cookies.get_dict()
        cookie = '; '.join([f'{key}={value}' for key, value in cookies.items()])
        return cookie
    except ConnectionError as e:
        print(f'ConnectionError: {e}')


def searchItemList(shopIds, pageNo, pageSize, cookie):
    url = "https://erp.91miaoshou.com/api/platform/shopee_global/item/item/searchItemList"
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'cookie': cookie
    }
    searchItemCondition = {
        'shopId': shopIds
    }
    data = {
        'pageNo': pageNo,
        'pageSize': pageSize,
        'status': 'onsale',
        **searchItemCondition
    }
    try:
        response = requests.post(url, data=data, headers=headers)
        res = json.loads(response.text)
        itemList = res.get('itemList', [])
        return itemList
    except ConnectionError as e:
        print(f'ConnectionError: {e}')


def getShopList(platform, cookie):
    url = "https://erp.91miaoshou.com/api/auth/shop/getShopList"
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'cookie': cookie
    }
    data = {
        'pageNo': 1,
        'pageSize': 100000,
        'platform': platform,
    }
    try:
        response = requests.post(url, data=data, headers=headers)
        res = json.loads(response.text)
        shopIds = [item['shopId'] for item in res['shopList']]
        return shopIds
    except ConnectionError as e:
        print(f'ConnectionError: {e}')


def get_account_shop_list(cookie):
    url = "https://erp.91miaoshou.com/api/platform/shopee/move/collect_box/get_account_shop_list"
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'cookie': cookie
    }
    try:
        response = requests.get(url, headers=headers)
        res = json.loads(response.text)
        shopIds = [item['shopId'] for item in res['shopList']]
        return shopIds
    except ConnectionError as e:
        print(f'ConnectionError: {e}')


if __name__ == "__main__":
    cookie = login('MX_hhb', 'MX_hhb250521')
    # getShopList('shopee', cookie)
    shopIds = get_account_shop_list(cookie)
    searchItemList(shopIds, 1, 5000, cookie)