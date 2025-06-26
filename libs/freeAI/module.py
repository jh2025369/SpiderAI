import requests
import os
import json
import imghdr
import execjs
import pyevaljs4
import subprocess
from io import BytesIO
from retrying import retry
from requests_toolbelt.multipart.encoder import MultipartEncoder

import sys
from pathlib import Path
# 将项目根目录添加到 Python 路径
sys.path.append(str(Path(__file__).parent.parent.parent))
from libs.miaoshou.module import login, get_account_shop_list, searchItemList


device_id = 'BRhI+0avq89b0kmU1N0eO/Q4bv7Ine52hJ0cYTji9vGfOLBkIyMDFkqICPYnn12stFQUZSsZEp81cYM/9jwlqhw=='
token = 'bTBd3lUsASzcSxVvfyLx/UxjyG2vOoeHPVp5n1QP9lnatrQFIn0vm1AR81kHIil8'
file_id = 'file-5f119412-c521-4a9f-a2f3-03e533a01c69'
session_id = 'aef29927-fdf4-4b70-845d-d0c4af0632fd'

def process_image_url(image_url):
    response = requests.get(image_url)
    image_data = response.content

    image_name = image_url.split("/")[-1]
    image_type = imghdr.what(None, h=image_data)
    if image_type not in ["jpeg", "png", "webp"]:
        raise ValueError("不支持的图片格式")
    
    filename = f'{image_name}.{image_type}'

    save_dir = "libs/freeAI/images"
    os.makedirs(save_dir, exist_ok=True)
    with open(f"{save_dir}/{filename}", "wb") as f:
        f.write(image_data)
    
    return filename, image_type, image_data


def get_device_id():
    url = 'https://fp-it-acc.portal101.cn/deviceprofile/v4'
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }

    node_command = [
        'node',
        'libs/freeAI/static/fp-1.min.js'
    ]
    result = subprocess.run(
        node_command,
        capture_output=True,
        text=True
    )
    data = json.loads(result.stdout)
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    res = json.loads(response.text).get('requestId', '')
    return res


def login(mobile, password, device_id):
    url = 'https://chat.deepseek.com/api/v0/users/login'
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'x-app-version': '20241129.1',
        'x-client-locale': 'zh_CN',
        'x-client-platform': 'web',
        'x-client-version': '1.2.0-sse-hint',
    }
    data = {
        'email': '',
        'mobile': mobile,
        'password': password,
        'area_code': '+86',
        'device_id': device_id,
        'os': 'web'
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    res = json.loads(response.text)
    user = res.get('data', {}).get('biz_data', {}).get('user', {}).get('token', {})
    return user


def create_pow_challenge(target_path, token):
    url = "https://chat.deepseek.com/api/v0/chat/create_pow_challenge"
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'x-app-version': '20241129.1',
        'x-client-locale': 'zh_CN',
        'x-client-platform': 'web',
        'x-client-version': '1.2.0-sse-hint',
        'Authorization': f'Bearer {token}'
    }
    data = {
        'target_path': target_path
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    res = json.loads(response.text)
    challenge = res.get('data', {}).get('biz_data', {}).get('challenge', {})
    return challenge


def do_solve_challenge(data):
    res = ''
    challenge = {
        'algorithm': data['algorithm'],
        'challenge': data['challenge'],
        'salt': data['salt'],
        'difficulty': data['difficulty'],
        'signature': data['signature'],
        'expireAt': data['expire_at'],
    }
    with open('libs/freeAI/static/245.90971a9967.js', 'r') as file:
        js_code = file.read()
        try:
            rt = pyevaljs4.compile_(js_code)
            # rt.eval(js_code)
            res = rt.call(
                'runChallenge',
                {
                    'type': "pow-challenge",
                    'challenge': challenge
                },
                async_js_func=True
            )
            rt.close()
        except Exception as e:
            print(f'Error executing JavaScript code: {e}')
    return res


def upload_file(image_url, token):
    challenge = create_pow_challenge('/api/v0/file/upload_file', token)
    data = do_solve_challenge(challenge)
    XDsPowResponse = ''
    with open('libs/freeAI/deepseek.js', 'r') as file:
        js_code = file.read()
        try:
            ctx = execjs.compile(js_code)
            XDsPowResponse = ctx.call('getXDsPowResponse', data['answer'], '/api/v0/file/upload_file')
        except Exception as e:
            print(f'Error executing JavaScript code: {e}')

    url = 'https://chat.deepseek.com/api/v0/file/upload_file'
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'x-app-version': '20241129.1',
        'x-client-locale': 'zh_CN',
        'x-client-platform': 'web',
        'x-client-version': '1.2.0-sse-hint',
        'x-thinking-enabled': '0',
        'x-ds-pow-response': XDsPowResponse,
        'Authorization': f'Bearer {token}',
    }

    filename, image_type, image_data = process_image_url(image_url)
    
    # # 构造multipart数据
    # boundary = '----WebKitFormBoundary' + ''.join(
    #     random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=16)
    # )
    
    # # 手动构造请求体
    # body = (
    #     f'--{boundary}\r\n'
    #     f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
    #     f'Content-Type: image/{image_type}\r\n\r\n'
    #     f'{requests.get(image_url).content.decode("latin1")}\r\n'
    #     f'--{boundary}--\r\n'
    # )
    # headers['content-type'] = f'multipart/form-data; boundary={boundary}'

    image_data = BytesIO(image_data)
    encoder = MultipartEncoder(
        fields={
            'file': (filename, image_data, f'image/{image_type}')
        }
    )
    headers['content-type'] = encoder.content_type

    response = requests.post(url, headers=headers, data=encoder)
    res = json.loads(response.text)
    file_id = res.get('data', {}).get('biz_data', {}).get('id', '')
    return file_id


@retry(stop_max_attempt_number=3, wait_fixed=2000)
def fetch_files(file_ids, token):
    url = 'https://chat.deepseek.com/api/v0/file/fetch_files'
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'x-app-version': '20241129.1',
        'x-client-locale': 'zh_CN',
        'x-client-platform': 'web',
        'x-client-version': '1.2.0-sse-hint',
        'Authorization': f'Bearer {token}',
    }
    params = [("file_ids", file_id) for file_id in file_ids]

    response = requests.get(url, headers=headers, params=params)
    res = json.loads(response.text)
    biz_data = res.get('data', {}).get('biz_data', {})

    for file in biz_data['files']:
        if file['status'] != 'SUCCESS':
            raise Exception('文件未加载成功')
        
    return True


def create_session(token):
    url = 'https://chat.deepseek.com/api/v0/chat_session/create'
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'x-app-version': '20241129.1',
        'x-client-locale': 'zh_CN',
        'x-client-platform': 'web',
        'x-client-version': '1.2.0-sse-hint',
        'Authorization': f'Bearer {token}',
    }
    data = {
        'character_id': None
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    res = json.loads(response.text)
    session_id = res.get('data', {}).get('biz_data', {}).get('id', '')
    return session_id


def completion(prompt, file_ids, session_id, parent_message_id, token):
    challenge = create_pow_challenge('/api/v0/chat/completion', token)
    data = do_solve_challenge(challenge)
    XDsPowResponse = ''
    with open('libs/freeAI/deepseek.js', 'r') as file:
        js_code = file.read()
        try:
            ctx = execjs.compile(js_code)
            XDsPowResponse = ctx.call('getXDsPowResponse', data['answer'], '/api/v0/file/upload_file')
        except Exception as e:
            print(f'Error executing JavaScript code: {e}')

    url = 'https://chat.deepseek.com/api/v0/chat/completion'
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'x-app-version': '20241129.1',
        'x-client-locale': 'zh_CN',
        'x-client-platform': 'web',
        'x-client-version': '1.2.0-sse-hint',
        'x-ds-pow-response': XDsPowResponse,
        'Authorization': f'Bearer {token}',
    }

    body = {
        'chat_session_id': session_id,
        'parent_message_id': parent_message_id,
        'prompt': prompt,
        'ref_file_ids': file_ids,
        'thinking_enabled': False,
        'search_enabled': False
    }

    response = requests.post(url, headers=headers, data=json.dumps(body), stream=True)
    message = ''
    is_message = False
    message_id = None
    try:
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                prefix, data = decoded_line.split(":", 1)
                if prefix == 'data':
                    data = json.loads(data)
                    if 'response_message_id' in data:
                        message_id = data['response_message_id']
                        continue

                    if 'p' in data:
                        if data['p'] == 'response/tips':
                            continue
                        if data['p'] == 'response/content':
                            is_message = True
                        elif data['p'] == 'response':
                            is_message = False
                    
                    if is_message:
                        message += data['v']
    finally:
        response.close()
        print(message)
    return message, message_id


if __name__ == "__main__":
    # cookie = login('username', 'password')
    # shopIds = get_account_shop_list(cookie)
    # itemList = searchItemList(shopIds, 1, 10, cookie)

    device_id = get_device_id()
    token = login('mobile', 'password', device_id)

    file_id = upload_file('https://s-cf-tw.shopeesz.com/file/sg-11134201-7rato-mb4py6ikbbdv44', token)
    if fetch_files([file_id], token):
        session_id = create_session(token)
        completion('描述一下这张图片', [file_id], session_id, None, token)