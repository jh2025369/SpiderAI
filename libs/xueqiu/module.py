import os
import requests
import json
import time
import execjs
from datetime import datetime
from selenium import webdriver

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))


cookie = ''

def md5(url):
    host = "xueqiu.com"
    code = 0
    for i in range(len(host)):
        code += ord(host[i])
    md5_code = code % (0x3 * -0x17a4 + 0xd * -0x579 + 0x209 * 0x59)

    md5_hash = ''
    with open("libs/xueqiu/xueqiu.js", 'r') as file:
        js_code = file.read()
        try:
            ctx = execjs.compile(js_code)
            md5_hash = ctx.call("md5", url)
        except Exception as e:
            print(f"Error executing JavaScript code: {e}")
    
    md5_url = f'{url}&md5__{md5_code}={md5_hash}'
    return md5_url


def request_xueqiu():
    driver = webdriver.Chrome()
    driver.get('https://xueqiu.com')
    cookies = driver.get_cookies()
    cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
    cookie_str = '; '.join([f'{key}={value}' for key, value in cookies_dict.items()])
    driver.quit()
    return cookie_str


def export_text(data, file_name):
    save_dir = 'libs/xueqiu/data'
    os.makedirs(save_dir, exist_ok=True)
    with open(f'{save_dir}/{file_name}.txt', 'w', encoding='utf-8') as f:
        for item in data.values():
            f.write(f"""
                created_at: {item['created_at']}\n
                title: {item['title']}\n
                description: {item['description']}\n
                text: {item['text']}\n
                comment: {item['comment']}\n
            """)


def search_comments(id, cookie):
    origin_url = f"https://xueqiu.com/statuses/v3/comments.json?id={id}&type=4&size=20&max_id=-1"
    url = md5(origin_url)

    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Connection': 'keep-alive',
        'cookie': cookie
    }
    try:
        response = requests.get(url, headers=headers, verify=False)
        data = json.loads(response.text)
        comments = data['comments']
        output = ''
        for comment in comments:
            output += f'{comment['text']}\n'
            if 'child_comments' in comment:
                for child_comment in comment['child_comments']:
                    output += f'{child_comment['text']}\n'
            output += '\n'
        return output
    except ConnectionError as e:
        print(f'ConnectionError: {e}')
        return ''


def search_status(symbol, count, cookie):
    origin_url = f"https://xueqiu.com/query/v1/symbol/search/status.json?count={count}&comment=0&symbol={symbol}&hl=0&source=all&sort=time&page=1&q=&type=11"
    url = md5(origin_url)

    headers = {
        'User-Agent': 'Mozilla/5.0',
        'cookie': cookie
    }

    message = {}
    try:
        response = requests.get(url, headers=headers)
        data = json.loads(response.text)
        for item in data['list']:
            id = item['id']
            message[id] = {
                'created_at': datetime.fromtimestamp(item['created_at'] // 1000),
                'title': item['title'],
                'description': item['description'],
                'text': item['text']
            }
    except ConnectionError as e:
        print(f'ConnectionError: {e}')
    
    return message


if __name__ == "__main__":
    symbol = '01810'
    cookie = request_xueqiu()
    message = search_status(symbol, 20, cookie)
    for key, value in message.items():
        comment = search_comments(key, cookie)
        value['comment'] = comment
        time.sleep(5)
    export_text(message, symbol)