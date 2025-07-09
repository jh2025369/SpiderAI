import os
import pyevaljs4
import requests
from math import ceil
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))


mapping = {
    'name': '名称',
    'current': '当前股价',
    'percent': '涨跌幅',
    'chg': '涨跌额',
    'turnoverRate': '换手率',
    'pct': '涨幅',
    'amount': '成交额',
    'famc': '流通市值',
    'peTtm': '市盈率(TTM)',
    'kline': 'k线'
}

gn_mapping = {
    '300816': '机器人概念',
    '300082': '军工',
    '301459': '华为概念',
}


def get_hexin_v(url):
    with open('libs/jqka/static/chameleon.1.7.min.1751908.js', 'r') as file:
        js_code = file.read()
        try:
            rt = pyevaljs4.compile_(js_code)
            hexin_v = rt.call(
                'getHexinV',
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


""" 概念资金排行 """
def search_gnzj(code, page):
    base_url = f'https://q.10jqka.com.cn/gn/detail/code/{code}/'
    diffRequest = ''
    data = []
    for i in range(page):
        url = base_url + diffRequest
        hexin_v = get_hexin_v(url)
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


if __name__ == "__main__":
    data = search_gnzj(300816, 5)
    export_text(data, '', gn_mapping[300816])