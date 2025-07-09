import requests
import json
import os
from datetime import datetime
from math import ceil

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))


mapping = {
    'name': '名称',
    'symbol': '股票编码',
    'date': '日期',
    'price': '价格',
    'rank': '排名',
    'changeRate': '涨跌幅',
    'netBuyAmt': '净买额',
    'buyAmt': '买入金额',
    'sellAmt': '卖出金额览量',
    'dealAmt': '成交金额',
}


def export_text(data, path_name, file_name, is_batch=None):
    save_dir = f'libs/eastmoney/data'
    if path_name != '':
        save_dir = f'libs/eastmoney/data/{path_name}'
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


""" 沪深资金 """
def search_CN_money(mutual_type, data, page, page_size):
    filter = f'(MUTUAL_TYPE="{mutual_type}")(TRADE_DATE=\'{data}\')'
    url = f'https://datacenter-web.eastmoney.com/web/api/data/v1/get?client=WEB&columns=ALL&filter={filter}&pageNumber={page}&pageSize={page_size}&reportName=RPT_MUTUAL_TOP10DEAL&sortColumns=RANK&sortTypes=1&source=WEB'
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    result = []
    try:
        response = requests.get(url, headers=headers)
        json_data = json.loads(response.text)
        data = json_data.get('result', {}).get('data', [])
        for item in data:
            result.append({
                'name': item['SECURITY_NAME'],
                'symbol': item['SECURITY_CODE'],
                'date': item['TRADE_DATE'],
                'price': item['CLOSE_PRICE'],
                'rank': item['RANK'],
                'changeRate': f'{item['CHANGE_RATE']}%',
                'dealAmt': f'{item['DEAL_AMT'] / 10**5}万'
            })
    except ConnectionError as e:
        print(f'ConnectionError: {e}')
    
    return result


""" 港股资金 """
def search_HK_money(mutual_type, data, page, page_size):
    filter = f'(MUTUAL_TYPE="{mutual_type}")(TRADE_DATE=\'{data}\')'
    url = f'https://datacenter-web.eastmoney.com/web/api/data/v1/get?client=WEB&columns=ALL&filter={filter}&pageNumber={page}&pageSize={page_size}&reportName=RPT_MUTUAL_TOP10DEAL&sortColumns=RANK&sortTypes=1&source=WEB'
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    result = []
    try:
        response = requests.get(url, headers=headers)
        data = json.loads(response.text)
        data = data.get('result', {}).get('data', [])
        for item in data:
            result.append({
                'name': item['SECURITY_NAME'],
                'symbol': item['SECURITY_CODE'],
                'date': item['TRADE_DATE'],
                'price': item['CLOSE_PRICE'],
                'rank': item['RANK'],
                'changeRate': f'{item['CHANGE_RATE']}%',
                'netBuyAmt': f'{item['NET_BUY_AMT'] / 10**5}万',
                'buyAmt': f'{item['BUY_AMT'] / 10**5}万',
                'sellAmt': f'{item['SELL_AMT'] / 10**5}万',
                'dealAmt': f'{item['DEAL_AMT'] / 10**5}万'
            })
    except ConnectionError as e:
        print(f'ConnectionError: {e}')
    
    return result


if __name__ == "__main__":
    current_date = datetime.now().strftime("%Y-%m-%d")
    # 沪股通
    result1 = search_CN_money('001', current_date, 1, 10)
    export_text(result1, '', '沪股通')
    # 深股通
    result2 = search_CN_money('003', current_date, 1, 10)
    export_text(result2, '', '深股通')
    # 港股通(沪)
    result3 = search_HK_money('002', current_date, 1, 10)
    export_text(result3, '', '港股通(沪)')
    # 港股通(深)
    result4 = search_HK_money('004', current_date, 1, 10)
    export_text(result4, '', '港股通(深)')

