import json
import os
import random
import pyevaljs4
import requests
from urllib.parse import quote
from math import ceil
from bs4 import BeautifulSoup

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))


mapping = {
    'name': '名称',
    'symbol': '股票编号',
    'current': '当前股价',
    'percent': '涨跌百分比',
    'chg': '涨跌额',
    'turnoverRate': '换手率',
    'pct': '振幅',
    'amount': '成交额',
    'famc': '流通市值',
    'peTtm': '市盈率(TTM)',
    'volume': '成交量',
    'kline': 'k线',
    'kline30': '30天k线',
    'ratio': '比例',
    'date': '时间',
    'bxzj': '30天北向资金净买入额',
    'bxzjbl': '北向资金持股占流通a股比例',
    'zlzj': '30天主力资金',
    'cje': '30天成交额',
    'shsl': '30天dde散户数量',
}

gn_mapping = {
    '300082': '军工',
    '300220': '期货概念',
    '300816': '机器人概念',
    '301085': '芯片概念',
    '301459': '华为概念',
    '301490': '泸股通',
    '301713': '中船系',
    '301997': '数字货币',
    '308624': '云游戏',
    '308829': '硅能源',
    '309119': '人形机器人',
}

hy_mapping = {
    '881124': '消费电子',
    '881145': '电力',
    '881279': '光伏设备',
    '881281': '电池',
}

def get_hexin_v(host, url):
    with open('libs/jqka/static/chameleon.1.7.min.1751908.js', 'r') as file:
        js_code = file.read()
        try:
            rt = pyevaljs4.compile_(js_code)
            hexin_v = rt.call(
                'getHexinV',
                host,
                url
            )
            rt.close()
        except Exception as e:
            rt.close()
            print(f'Error executing JavaScript code: {e}')

    return hexin_v


def export_text(data, path_name, file_name, is_batch=None):
    save_dir = f'libs/jqka/data'
    if path_name != '':
        save_dir = f'libs/jqka/data/{path_name}'
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
                        f.write(f'{mapping[key]}: [')
                        for child_item in item[key]:
                            f.write('\n')
                            f.write('  {\n')
                            for child_key, child_value in child_item.items():
                                f.write(f'    {mapping[child_key]}: {child_value}\n')
                            f.write('  },')
                        f.write(']\n')
                    else:
                        f.write(f'{mapping[key]}: {item[key]}\n')
                f.write('\n')


""" 概念资金排行 """
def search_gnzj(code, page):
    host = 'q.10jqka.com.cn'
    base_url = f'https://q.10jqka.com.cn/gn/detail/code/{code}/'
    diffRequest = ''
    data = []
    for i in range(page):
        url = base_url + diffRequest
        hexin_v = get_hexin_v(host, url)
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'hexin-v': hexin_v
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        target = soup.select_one('.m-pager-table .cur a[field]')
        field = target.get('field')
        diffRequest = f'field/{field}/order/desc/page/{i + 2}/ajax/1/'

        table = soup.find('table', {'class': 'm-table m-pager-table'})
        rows = table.find('tbody').find_all('tr')

        for row in rows:
            cells = row.text.split('\n')[1:]
            if len(cells) == 0:
                continue
            data.append({
                'name': cells[2],
                'current': cells[3],
                'percent': cells[4],
                'chg': cells[5],
                'turnoverRate': cells[7],
                'pct': cells[9],
                'amount': cells[10],
                'famc': cells[12],
                'peTtm': cells[13]
            })

    return data


""" 行业资金排行 """
def search_hyzj(code, page):
    host = 'q.10jqka.com.cn'
    base_url = f'https://q.10jqka.com.cn/thshy/detail/code/{code}/'
    diffRequest = ''
    data = []
    for i in range(page):
        url = base_url + diffRequest
        hexin_v = get_hexin_v(host, url)
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'hexin-v': hexin_v
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        target = soup.select_one('.m-pager-table .cur a[field]')
        field = target.get('field')
        diffRequest = f'field/{field}/order/desc/page/{i + 2}/ajax/1/'

        table = soup.find('table', {'class': 'm-table m-pager-table'})
        rows = table.find('tbody').find_all('tr')

        for row in rows:
            cells = row.text.split('\n')[1:]
            if len(cells) == 0:
                continue
            data.append({
                'name': cells[2],
                'current': cells[3],
                'percent': cells[4],
                'chg': cells[5],
                'turnoverRate': cells[7],
                'pct': cells[9],
                'amount': cells[10],
                'famc': cells[12],
                'peTtm': cells[13]
            })

    return data


def search_robot_data(question):
    host = 'www.iwencai.com'
    href = f'https://www.iwencai.com/unifiedwap/result?typed=1&preParams=&ts=1&f=1&qs=1&selfsectsn=&querytype=&searchfilter=&tid=stockpick&w={quote(question)}'
    url = 'https://www.iwencai.com/customized/chart/get-robot-data'
    hexin_v = get_hexin_v(host, href)
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'content-type': 'application/json',
        'hexin-v': hexin_v
    }

    characters = 'abcdefghijklmnopqrstuvwxyz0123456789'
    s = random.choices(characters, k=32)
    key = ''.join(s)

    info = {
        'urp': {
            'scene': 1,
            'company': 1,
            'business': 1,
        },
        'contentType': 'json',
        'searchInfo': True,
    }
    log_info = {
        'input_type': 'click'
    }
    data = {
        'add_info': json.dumps(info),
        'block_list': '',
        'log_info': json.dumps(log_info),
        'page': 1,
        'perpage': 50,
        'query_area': '',
        'question': question,
        'rsh': f'Ths_iwencai_Xuangu_{key}',
        'secondary_intent': '',
        'source': 'Ths_iwencai_Xuangu',
        'version': '2.0'
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    json_data = json.loads(response.text)
    result = {}
    answer = json_data.get('data', {}).get('answer')
    if len(answer) > 0:
        txt = answer[0]['txt']
        if len(txt) == 0:
            return None
        components = txt[0]['content']['components']

        bxzj = []
        bxzjbl = []
        zlzj = []
        cje = []
        shsl = []
        kline = []
        for component in components:
            if component['show_type'] != 'barline3' and component['show_type'] != 'tab4':
                continue

            if 'tab_list' in component:
                tab_list = component['tab_list']
                if len(tab_list) >= 1 and tab_list[0]['tab_name'] == '北向资金流向':
                    list_ = tab_list[0]['list']
                    if len(list_) >= 2 and 'data' in list_[1] and 'datas' in list_[1]['data']:
                        datas = list_[1]['data']['datas']
                        for data in datas:
                            bxzj.append(data['北向资金净买入额'])
                
                if len(tab_list) >= 2 and tab_list[1]['tab_name'] == '北向资金持股比例':
                    list_ = tab_list[1]['list']
                    if len(list_) >= 1 and 'data' in list_[0] and 'datas' in list_[0]['data']:
                        datas = list_[0]['data']['datas']
                        for data in datas:
                            bxzjbl.append({
                                'date': data['时间'],
                                'ratio': data['北向资金持股占流通a股比例']
                            })
            
            if 'data' in component and 'datas' in component['data']:
                datas = component['data']['datas']
                for data in datas:
                    if '主力资金' in data:
                        zlzj.append(data['主力资金'])
                    
                    if '成交额' in data:
                        cje.append(data['成交额'])
                    
                    if 'dde散户数量' in data:
                        shsl.append(data['dde散户数量'])
                    
                    if '股价走势' in data:
                        kline.append(data['股价走势'])
        
        result['bxzj'] = ','.join(map(str, bxzj))
        result['bxzjbl'] = bxzjbl
        result['zlzj'] = ','.join(map(str, zlzj))
        result['cje'] = ','.join(map(str, cje))
        result['shsl'] = ','.join(map(str, shsl))
        result['kline30'] = ','.join(map(str, kline))
    
    return result


if __name__ == "__main__":
    # data = search_gnzj(300816, 5)
    # export_text(data, '', gn_mapping['300816'])
    # data = search_hyzj(881279, 5)
    # export_text(data, '', hy_mapping['881279'])
    data = search_robot_data('新亚电子')
    export_text([data], '', '新亚电子')