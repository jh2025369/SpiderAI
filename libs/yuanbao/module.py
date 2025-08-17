import json
import requests
import pyevaljs4
from playwright.sync_api import sync_playwright

import sys
from pathlib import Path
# 将项目根目录添加到 Python 路径
sys.path.append(str(Path(__file__).parent.parent.parent))
from services.redis_service import RedisService


def cookie_string_to_dict(cookie_str, domain):
    cookies = []
    for pair in cookie_str.split('; '):
        name, value = pair.split('=', 1)
        cookies.append({
            'name': name,
            'value': value,
            'domain': domain,
            'path': '/', 
        })
    return cookies


def cookie_string_to_dict_simple(cookie_str):
    cookies = {}
    for pair in cookie_str.split('; '):
        name, value = pair.split('=', 1)
        cookies[name] = value
    return cookies


def require_yuanbao(agent_id):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        cookie = RedisService.get_cookie('test')

        if cookie:
            storage_state={
                "cookies": cookie_string_to_dict(cookie, '.tencent.com')
            }
            context = browser.new_context(storage_state=storage_state)
            page = context.new_page()
        else:
            page = browser.new_page()
        
        initial_url = f'https://yuanbao.tencent.com/chat/{agent_id}'
        page.goto(initial_url)
        
        input('请手动完成扫码登录...')
            
        def on_response(response):
            if response.url.startswith('https://yuanbao.tencent.com/api/anon/login'):
                try:
                    user_info = response.json()
                except:
                    print('响应体:', response.text())
        
        page.on('response', on_response)
        
        try:
            final_url = page.url
            print('登录后的URL:', final_url)
            
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(final_url)
            params = parse_qs(parsed.query)

            cookies = page.context.cookies()
            cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
            cookie_str = '; '.join([f'{key}={value}' for key, value in cookies_dict.items()])
            RedisService.set_cookie('test', cookie_str)

            # localStorage = page.evaluate('() => { const items = {}; '
            #                  'for (let i = 0; i < localStorage.length; i++) { '
            #                  'const key = localStorage.key(i); '
            #                  'items[key] = localStorage.getItem(key); } '
            #                  'return items; }')
            # RedisService.set_hset('test:localStorage', localStorage)

            # sessionStorage = page.evaluate('() => { const items = {}; '
            #                    'for (let i = 0; i < sessionStorage.length; i++) { '
            #                    'const key = sessionStorage.key(i); '
            #                    'items[key] = sessionStorage.getItem(key); } '
            #                    'return items; }')
            # RedisService.set_hset('test:sessionStorage', sessionStorage)
            
            return cookie_str
            
        except Exception as e:
            print('等待登录超时或出错:', e)
            return None
        finally:
            browser.close()


def set_cache(agent_id):
    cookie = RedisService.get_cookie('test')
    with open('libs/yuanbao/main.js', 'r', encoding='utf-8') as file:
        js_code = file.read()
        try:
            rt = pyevaljs4.compile_(js_code)
            rt.call('set_cache', agent_id, cookie)
            rt.call('requireCommonJSModule')
            res = rt.call('get_user_info', async_js_func=True)
            rt._node.terminate()
            rt.close()
        except Exception as e:
            rt.close()
            print(f'Error executing JavaScript code: {e}')
            
    return res


def get_user_info(cookie):
    url = 'https://yuanbao.tencent.com/api/getuserinfo'
    cookie_dict = cookie_string_to_dict_simple(cookie)
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'cookie': cookie
        # 'x-agentid': agent_id,
        # 'x-commit-tag': 'f8f5df02',
        # 'x-device-id': cookie_dict['_qimei_uuid42'],
        # 'x-hy106': '',
        # 'x-hy92': cookie_dict['_qimei_h38'],
        # 'x-hy93': cookie_dict['_qimei_uuid42'],
        # 'x-instance-id': '5',
        # 'x-language': 'zh-CN',
        # 'x-os_version': 'Windows(10)-Blink',
        # 'x-platform': 'win',
        # 'x-requested-with': 'XMLHttpRequest',
        # 'x-source': 'web',
        # 'x-webdriver': '0',
        # 'x-webversion': '2.32.6',
        # 'x-ybuitest': '0',
    }
    try:
        response = requests.get(url, headers=headers)
        json_data = json.loads(response.text)
    except ConnectionError as e:
        print(f'ConnectionError: {e}')
    
    return json_data


def create_sation(cookie, agent_id):
    url = 'https://yuanbao.tencent.com/api/user/agent/conversation/create'
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'cookie': cookie
    }
    data = {
        'agentId': agent_id
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        json_data = json.loads(response.text)
        if 'id' in json_data:
            return json_data['id']
    except ConnectionError as e:
        print(f'ConnectionError: {e}')
    
    return None


def update_model(cookie, cid):
    url = 'https://yuanbao.tencent.com/api/user/agent/conversation/updateModel'
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'cookie': cookie
    }
    chat_model_ext_info = {
        'modelId': 'deep_seek_v3',
        'subModelId': 'deep_seek',
        'supportFunctions': {
            'internetSearch': 'autoInternetSearch'
        }
    }
    data = {
        'chatModelExtInfo': json.dumps(chat_model_ext_info),
        'chatModelId': 'deep_seek_v3',
        'cid': cid
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        json_data = json.loads(response.text)
    except ConnectionError as e:
        print(f'ConnectionError: {e}')
    
    return json_data


def stop_conversation(cookie, cid):
    url = f'https://yuanbao.tencent.com/api/stop/conversation/{cid}'
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'cookie': cookie
    }
    try:
        response = requests.post(url, headers=headers)
        text = response.text
    except ConnectionError as e:
        print(f'ConnectionError: {e}')
    
    return text


def chat(cookie, agent_id, cid, prompt):
    url = f'https://yuanbao.tencent.com/api/chat/{cid}'
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'cookie': cookie
    }
    options = {
        'backendUpdateFlag': 2,
        'intentionStatus': True,
        'needIntentionModel': True
    }
    data = {
        'agentId': agent_id,
        'chatModelId': 'deep_seek_v3',    # ['deep_seek_v3', 'deep_seek']
        'displayPromptType': 1,
        'isAtomInput': False,
        'model': 'gpt_175B_0404',
        'options': options,
        'plugin': 'Adaptive',
        'Prompt': prompt,
        'skillId': 'unique-skill-aisearch',
        'supportFunctions': ['autoInternetSearch'],    # ['autoInternetSearch', 'openInternetSearch', 'closeInternetSearch']
        'supportHint': 1,
        'version': 'v2',
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data), stream=True)
        result = ''
        try:
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if 'data' in decoded_line and 'type' in decoded_line and 'msg' in decoded_line:
                        json_str = decoded_line.split('data: ')[1]
                        data_obj = json.loads(json_str)
                        result += data_obj.get('msg', '')
        finally:
            print(result)
            response.close()
    except ConnectionError as e:
        print(f'ConnectionError: {e}')
    
    return result


if __name__ == '__main__':
    # config = {
    #     'REDIS_HOST': '127.0.0.1',
    #     'REDIS_PORT': 6379,
    #     'REDIS_DB': 0,
    #     'REDIS_PASSWORD': '123'
    # }
    # RedisService.init_redis(config)
    # cookie = RedisService.get_cookie('test')
    
    agent_id = 'naQivTmsDa'
    cookie = require_yuanbao(agent_id)
    # set_cache(cookie)

    cid = create_sation(cookie, agent_id)
    chat(cookie, agent_id, cid, '抓取股票数据后如何做量化')
    # get_user_info(cookie)
    # update_model(cookie, cid)
    # stop_conversation(cookie, cid)