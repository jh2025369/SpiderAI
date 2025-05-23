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


def login():
    global cookie
    url = "https://erp.91miaoshou.com/api/auth/account/login"
    data = loginParam('MX_hhb', 'MX_hhb250521')
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'X-BreadCrumb': 'system-login'
    }
    try:
        response = requests.post(url, data=data, headers=headers)
        res = json.loads(response.text)
        cookies = response.cookies.get_dict()
        cookie = '; '.join([f'{key}={value}' for key, value in cookies.items()])
        print("获取到的Cookies:", cookie)
    except ConnectionError as e:
        print(f'ConnectionError: {e}')


def searchItemList():
    global cookie
    url = "https://erp.91miaoshou.com/api/platform/shopee_global/item/item/searchItemList"
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'cookie': cookie
    }
    searchItemCondition = {
        'shopId': [3849629]
    }
    data = {
        'pageNo': 1,
        'pageSize': 2000,
        'status': 'onsale',
        **searchItemCondition
    }
    try:
        response = requests.post(url, data=data, headers=headers)
        res = json.loads(response.text)
        print(res)
    except ConnectionError as e:
        print(f'ConnectionError: {e}')


if __name__ == "__main__":
    login()
    searchItemList()