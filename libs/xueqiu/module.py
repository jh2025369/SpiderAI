import os
import requests
import json
import time
import execjs
from math import ceil
from urllib.parse import quote
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))


mapping = {
    'createdAt': '时间',
    'title': '标题',
    'description': '描述',
    'text': '内容',
    'replyCount': '回复数',
    'viewCount': '浏览量',
    'comment': '评论',
    'name': '名称',
    'symbol': '股票编号',
    'current': '当前股价',
    'percent': '涨跌幅',
    'chg': '涨跌额',
    'exchange': '交易类型',
    'pct': '涨幅',
    'follow': '关注数',
    'encode': '分类编码',
    'relevant': '相关股票',
    'change': '价格变化绝对值',
    'volume': '成交量',
    'industry': '工业名称',
    'industrystocks': '工业股票',
    'tdDate': '时间',
    'buyAmt': '买入额度',
    'sellAmt': '卖出额度',
    'netAmt': '净额',
    'ratio': '占比',
    'kline': 'k线',
    'amount': '成交额',
    'turnoverRate': '换手率',
    'peTtm': '市盈率(TTM)',
}

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
            print(f'Error executing JavaScript code: {e}')
    
    md5_url = f'{url}&md5__{md5_code}={md5_hash}'
    return md5_url


def request_xueqiu():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://xueqiu.com')
    cookies = driver.get_cookies()
    cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
    cookie_str = '; '.join([f'{key}={value}' for key, value in cookies_dict.items()])
    driver.quit()
    return cookie_str


def export_text(data, path_name, file_name, is_batch=None):
    save_dir = f'libs/xueqiu/data'
    if path_name != '':
        save_dir = f'libs/xueqiu/data/{path_name}'
    os.makedirs(save_dir, exist_ok=True)

    batch_size = 80
    total_batches = ceil(len(data) / batch_size)

    for batch_num in range(total_batches):
        start = batch_num * batch_size
        end = start + batch_size
        batch_data = data[start:end]

        target_path = f'{save_dir}/{file_name}.txt'
        if is_batch:
            target_path = f'{save_dir}/{file_name}-{batch_num + 1}.txt'
        
        with open(target_path, 'w', encoding='utf-8') as f:
            for item in batch_data:
                for key in item:
                    if type(item[key]) == list:
                        f.write(f'{mapping[key]}: [\n')
                        for child_item in item[key]:
                            f.write('  {\n')
                            for child_key, child_value in child_item.items():
                                f.write(f'    {mapping[child_key]}: {child_value}\n')
                            f.write('  },\n')
                        f.write(']\n')
                    else:
                        f.write(f'{mapping[key]}: {item[key]}\n')
                f.write('\n')


def search_comments(cookie, id):
    origin_url = f'https://xueqiu.com/statuses/v3/comments.json?id={id}&type=4&size=20&max_id=-1'
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


#source: all user trans
def search_status(cookie, symbol, page, count, source):
    origin_url = f'https://xueqiu.com/query/v1/symbol/search/status.json?count={count}&comment=0&symbol={symbol}&hl=0&source={source}&sort=time&page={page}&q=&type=11'
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
            track = json.loads(item['trackJson'])
            message[id] = {
                'createdAt': datetime.fromtimestamp(item['created_at'] // 1000),
                'title': item['title'],
                'description': item['description'],
                # 'text': item['text'],
                'replyCount': track.get('reply_count', 0),
                'viewCount': item['view_count']
            }
    except ConnectionError as e:
        print(f'ConnectionError: {e}')
    
    return message


def search_stock_timeline(cookie, symbol, page, count, source):
    origin_url = f'https://xueqiu.com/statuses/stock_timeline.json?symbol_id={symbol}&count={count}&source={quote(source)}&page={page}'
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
                'createdAt': datetime.fromtimestamp(item['created_at'] // 1000),
                'title': item['title'],
                'description': item['description']
            }
    except ConnectionError as e:
        print(f'ConnectionError: {e}')
    
    return message


def search_relevant(cookie, symbol):
    url = f'https://stock.xueqiu.com/v5/stock/quote/relevant.json?symbol={symbol}'
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'cookie': cookie
    }
    message = []
    try:
        response = requests.get(url, headers=headers)
        data = json.loads(response.text)
        items = data['data']['items']
        for item in items:
            message.append({
                'name': item['name'],
                'symbol': item['symbol'],
                'current': item['current'],
                'percent': item['percent']
            })
    except ConnectionError as e:
        print(f'ConnectionError: {e}')
    
    return message


def search_stock(cookie, symbol):
    url = f'https://stock.xueqiu.com/v5/stock/quote.json?symbol={symbol}&extend=detail'
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'cookie': cookie
    }
    message = {}
    try:
        response = requests.get(url, headers=headers)
        data = json.loads(response.text)
        quote = data['data']['quote']
        message = {
            'name': quote['name'],
            'symbol': quote['symbol'],
            'current': quote['current'],
            'percent': quote['percent'],
            'volume': quote['volume'],
            'exchange': quote['exchange']
        }
    except ConnectionError as e:
        print(f'ConnectionError: {e}')
    
    return message


def search_stock_by_name(cookie, name):
    origin_url = f'https://xueqiu.com/query/v1/suggest_stock.json?q={name}'
    url = md5(origin_url)
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'cookie': cookie
    }
    code = ''
    try:
        response = requests.get(url, headers=headers)
        data = json.loads(response.text)
        items = data['data']
        if items and len(items) > 0:
            code = items[0]['code']
    except ConnectionError as e:
        print(f'ConnectionError: {e}')
    
    return code


def search_longhu(cookie, symbol, page, size):
    url = f'https://stock.xueqiu.com/v5/stock/capital/longhu.json?symbol={symbol}&page={page}&size={size}'
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'cookie': cookie
    }
    message = []
    try:
        response = requests.get(url, headers=headers)
        data = json.loads(response.text)
        items = data['data']['items']
        for item in items:
            for child in item:
                td_date = datetime.fromtimestamp(child['td_date'] // 1000)
                branches = child['branches']
                for branch in branches:
                    message.append({
                        'tdDate': td_date,
                        'name': branch['branch_name'],
                        'buyAmt': branch['buy_amt'],
                        'sellAmt': branch['sell_amt'],
                        'netAmt': branch['net_amt'],
                        'ratio': branch['ratio']
                    })
    except ConnectionError as e:
        print(f'ConnectionError: {e}')
    
    return message


def search_kline(cookie, symbol, begin, count):
    url = f'https://stock.xueqiu.com/v5/stock/chart/kline.json?symbol={symbol}&begin={begin}&period=day&type=before&count={count}&indicator=kline,pe,pb,ps,pcf,market_capital,agt,ggt,balance'
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'cookie': cookie
    }
    message = []
    try:
        response = requests.get(url, headers=headers)
        data = json.loads(response.text)
        items = data.get('data', {}).get('item', [])
        for item in items:
            message.append(item[5])
    except ConnectionError as e:
        print(f'ConnectionError: {e}')
    
    return message


def search_stock_list(cookie, code, type_=1):
    origin_url = f'https://xueqiu.com/stock/industry/stockList.json?code={code}&type={type_}&size=100'
    url = md5(origin_url)
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'cookie': cookie
    }
    result = {}
    try:
        response = requests.get(url, headers=headers)
        data = json.loads(response.text)
        result['industryname'] = data['industryname']
        items = data['industrystocks']
        stocks = []
        for item in items:
            stocks.append({
                'name': item['name'],
                'symbol': item['symbol'],
                'current': item['current'],
                'exchange': item['exchange'],
                'percent': item['percentage'],
                'change': item['change'],
                'volume': item['volume']
            })
        result['industrystocks'] = stocks
    except ConnectionError as e:
        print(f'ConnectionError: {e}')
    
    return result


""" 热门股票
:param type: 10 全球 11 美股 12 沪深 13 港股
"""
def search_hot_stock(cookie, type, size):
    origin_url = f'https://stock.xueqiu.com/v5/stock/hot_stock/list.json?size={size}&_type={type}&type={type}'
    url = md5(origin_url)
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'cookie': cookie
    }
    message = []
    try:
        response = requests.get(url, headers=headers)
        data = json.loads(response.text)
        items = data['data']['items']
        for item in items:
            message.append({
                'name': item['name'],
                'symbol': item['symbol'],
                'current': item['current'],
                'percent': item['percent'],
                'exchange': item['exchange']
            })
    except ConnectionError as e:
        print(f'ConnectionError: {e}')
    
    return message


""" 股票分类
:param category: cn 沪深 hk 港股 us 美股
"""
def search_industries(cookie, category):
    url = f'https://stock.xueqiu.com/v5/stock/screener/industries.json?category={category}'
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'cookie': cookie
    }
    message = []
    try:
        response = requests.get(url, headers=headers)
        data = json.loads(response.text)
        items = data['data']['industries']
        for item in items:
            message.append({
                'name': item['name'],
                'encode': item['encode'],
            })
    except ConnectionError as e:
        print(f'ConnectionError: {e}')
    
    return message


""" 行情排行
:param market: CN 沪深 HK 港股 US 美股
:param type: sh_sz_bj 沪深 sh_sz 泸深科创 sha 泸A shb 泸B sza 深A szb 深B cyb 创业板 zxb 中小板 hk 港股 us 美股
:param page: 页码
:param size: 每页大小
:param order_by: percent 涨跌幅 volume 成交量 amount 成交额 current_year_percent 年涨跌
:param order: asc desc
:param ind_code: 分类编码
"""
def search_market_ranking(cookie, market, type_, page, size, order_by, order, ind_code=None):
    url = f'https://stock.xueqiu.com/v5/stock/screener/quote/list.json?size={size}&page={page}&order_by={order_by}&order={order}&market={market}&type={type_}&_=1751303950327'
    if ind_code:
        url += f'&ind_code={ind_code}'
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'cookie': cookie
    }
    message = []
    try:
        response = requests.get(url, headers=headers)
        data = json.loads(response.text)
        items = data['data']['list']
        for item in items:
            message.append({
                'name': item['name'],
                'symbol': item['symbol'],
                'current': item['current'],
                'percent': item['percent'],
                'chg': item['chg'],
                'volume': item['volume'],
                'amount': item['amount'],
                'turnoverRate': item['turnover_rate'],
                'peTtm': item['pe_ttm'],
            })
    except ConnectionError as e:
        print(f'ConnectionError: {e}')
    
    return message


""" 分类排行
:param category: CN 沪深 HK 港股 US 美股
:param order_by: follow7d 关注新增 follow 关注热门 tweet7d 讨论新增 tweet 讨论热门 deal7d 交易新增 deal 交易热门
:param order: asc desc
"""
def search_class_ranking(cookie, category, page, size, order_by, order):
    url = f'https://stock.xueqiu.com/v5/stock/screener/screen.json?page={page}&only_count=0&size={size}&category={category}&order_by={order_by}&order={order}'
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'cookie': cookie
    }
    message = []
    try:
        response = requests.get(url, headers=headers)
        data = json.loads(response.text)
        items = data['data']['list']
        for item in items:
            message.append({
                'name': item['name'],
                'symbol': item['symbol'],
                'current': item['current'],
                'pct': item['pct'],
                'follow': item[order_by]
            })
    except ConnectionError as e:
        print(f'ConnectionError: {e}')
    
    return message


if __name__ == "__main__":
    now = datetime.now().replace(microsecond=0)
    timestamp_ms = int(now.timestamp() * 1000)
    symbol = '01810'
    # cookie = request_xueqiu()
    # message = {}
    # for i in range(1, 5):
    #     status = search_status(cookie, symbol, i, 20, 'all')
    #     message = {**message, **status}
    # for key, value in message.items():
    #     if value['replyCount'] > 0:
    #         comment = search_comments(cookie, key)
    #         value['comment'] = comment
    #         time.sleep(10)
    # export_text(list(message.values()), symbol, symbol, True)
    # message = search_stock_timeline(cookie, symbol, 1, 20, '自选股新闻')
    # export_text(list(message.values()), symbol, 'stock')
    # message = search_relevant(cookie, symbol)
    # export_text(message, symbol, 'relevant')
    # message = search_hot_stock(cookie, 12, 20)
    # export_text(message, '', 'hot_stock')

    industries = search_industries(cookie, 'cn')
    for industry in industries:
        name = industry['name']
        if name not in ['电池']:
            continue
        encode = industry['encode']

        categories = {
            'sh_sz_bj': 'CN',
            # 'sh_sz': 'CN',
            # 'sha': 'CN',
            # 'shb': 'CN',
            # 'sza': 'CN',
            # 'szb': 'CN',
            # 'cyb': 'CN',
            # 'zxb': 'CN',
            # 'hk': 'HK',
            # 'us': 'US'
        }
        for key, value in categories.items():
            stocks = search_market_ranking(cookie, value, key, 1, 20, 'percent', 'desc', encode)
            for stock in stocks:
                kline = search_kline(cookie, stock['symbol'], timestamp_ms, -284)
                stock['kline'] = ','.join(map(str, kline))
            export_text(stocks, f'ranking/{key}', name)

    # categories = {
    #     'follow7d': 'CN',
    #     'follow': 'CN',
    #     # 'tweet7d': 'HK',
    #     # 'tweet': 'HK',
    #     # 'deal7d': 'US',
    #     # 'deal': 'US'
    # }
    # for key, value in categories.items():
    #     message = search_class_ranking(cookie, value, 1, 20, key, 'desc')
    #     export_text(message, 'ranking', key)