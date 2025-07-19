import os
import random
import re
import time
from flask import Blueprint, request
from datetime import datetime
import libs.freeAI.module as freeAI
import libs.xueqiu.module as xueqiu
import libs.jqka.module as jqka
from services.redis_service import RedisService

xueqiu_bp = Blueprint('xueqiu', __name__)

@xueqiu_bp.route('/get_cookie', methods=['GET'])
def get_cookie():
    user_id = request.args.get('userId')
    cookie = xueqiu.request_xueqiu()
    RedisService.set_cookie(user_id, cookie, 3600 * 24 * 3)
    return {
        'status': 'success',
        'cookie': cookie
    }


@xueqiu_bp.route('/get_status', methods=['GET'])
def get_status():
    user_id = request.args.get('userId')
    symbol = request.args.get('symbol')
    page = int(request.args.get('page'))
    count = int(request.args.get('count'))
    source = request.args.get('source', 'all')
    cookie = RedisService.get_cookie(user_id)
    if not cookie:
        return {
            'status': 'error',
            'message': 'Please login first.'
        }
    
    try:
        message = {}
        for i in range(1, page + 1):
            status = xueqiu.search_status(cookie, symbol, i, count, source)
            message = {**message, **status}
        for key, value in message.items():
            if value['replyCount'] > 0:
                comment = xueqiu.search_comments(cookie, key)
                value['comment'] = comment
                time.sleep(5)
        xueqiu.export_text(list(message.values()), symbol, symbol, True)
        return {
            'status': 'success',
            'items': message
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }
    

@xueqiu_bp.route('/get_longhu', methods=['GET'])
def get_longhu():
    user_id = request.args.get('userId')
    symbol = request.args.get('symbol')
    page = request.args.get('page')
    size = request.args.get('size')
    cookie = RedisService.get_cookie(user_id)
    if not cookie:
        return {
            'status': 'error',
            'message': 'Please login first.'
        }
    
    try:
        message = xueqiu.search_longhu(cookie, symbol, page, size)
        xueqiu.export_text(message, symbol, 'longhu', True)
        return {
            'status': 'success',
            'items': message
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }


@xueqiu_bp.route('/get_hot_stock', methods=['GET'])
def get_hot_stock():
    user_id = request.args.get('userId')
    type_ = request.args.get('type', 12)
    size = request.args.get('size', 20)
    cookie = RedisService.get_cookie(user_id)
    if not cookie:
        return {
            'status': 'error',
            'message': 'Please login first.'
        }
    
    now = datetime.now().replace(microsecond=0)
    timestamp_ms = int(now.timestamp() * 1000)
    
    try:
        result = []
        hot_stocks = xueqiu.search_hot_stock(cookie, type_, size)
        for item in hot_stocks:
            symbol = item['symbol']
            stock = xueqiu.search_stock(cookie, symbol)
            kline = xueqiu.search_kline(cookie, symbol, timestamp_ms, -60)
            stock['kline'] = ','.join(map(str, kline))

            relevant = xueqiu.search_relevant(cookie, symbol)
            for relstock in relevant:
                kline = xueqiu.search_kline(cookie, relstock['symbol'], timestamp_ms, -60)
                relstock['kline'] = ','.join(map(str, kline))
            stock['relevant'] = relevant

            # stock_res = search_stock_list(cookie, symbol)
            # stock['industry'] = stock_res['industryname']
            # industrystocks = stock_res['industrystocks']
            # for industrystock in industrystocks:
            #     kline = search_kline(cookie, industrystock['symbol'], timestamp_ms, -60)
            #     industrystock['kline'] = ','.join(map(str, kline))
            #     # time.sleep(5)
            # stock['industrystocks'] = industrystocks

            result.append(stock)
        xueqiu.export_text(result, 'hot_stock', 'hot_stock')
        return {
            'status': 'success',
            'items': result
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }
    

@xueqiu_bp.route('/recommend_industry_stock', methods=['GET'])
def recommend_industry_stock():
    user_id = request.args.get('userId')
    type_ = request.args.get('type')
    cookie = RedisService.get_cookie(user_id)
    token = RedisService.get_hset(f'user:{user_id}', 'token')
    if not cookie or not token:
        return {
            'status': 'error',
            'message': 'Please login first.'
        }
    
    now = datetime.now().replace(microsecond=0)
    timestamp_ms = int(now.timestamp() * 1000)
    
    try:
        industries = xueqiu.search_industries(cookie, 'cn')
        for industry in industries:
            name = industry['name']
            if name != type_:
                continue
            encode = industry['encode']

            key = 'sh_sz'
            stocks = xueqiu.search_market_ranking(cookie, 'CN', key, 1, 30, 'percent', 'desc', encode)
            for stock in stocks:
                kline = xueqiu.search_kline(cookie, stock['symbol'], timestamp_ms, -100)
                stock['kline'] = ','.join(map(str, kline))
            xueqiu.export_text(stocks, f'ranking/{key}', name)

            prompt = f'分析{type_}行业股票走向，推荐近两天会涨的股票，给出购买价格'
            encoder = freeAI.process_local_file(f'libs/xueqiu/data/ranking/{key}/{type_}.txt')
            file_id = freeAI.upload_file(encoder, token)
            if freeAI.fetch_files([file_id], token):
                session_id = freeAI.create_session(token)
                result, message_id = freeAI.completion(prompt, [file_id], session_id, None, token)
                RedisService.update_hset(f'{user_id}:session', session_id, message_id)
                # RedisService.update_hset(f'{user_id}:message', session_id, result)
            
            return {
                'status': 'success',
                'session_id': session_id,
                'result': result
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }
    

@xueqiu_bp.route('/quantify_stock', methods=['GET'])
def quantify_stock():
    user_id = request.args.get('userId')
    symbol = request.args.get('symbol')
    page = int(request.args.get('page'))
    count = int(request.args.get('count'))
    source = request.args.get('source', 'all')
    session_id = request.args.get('sessionId')
    cookie = RedisService.get_cookie(user_id)
    token = RedisService.get_hset(f'user:{user_id}', 'token')
    if not cookie or not token:
        return {
            'status': 'error',
            'message': 'Please login first.'
        }
    
    now = datetime.now().replace(microsecond=0)
    timestamp_ms = int(now.timestamp() * 1000)
    
    try:
        message = {}

        stock = xueqiu.search_stock(cookie, symbol)
        # kline = xueqiu.search_kline(cookie, symbol, timestamp_ms, -60)
        # stock['kline'] = ','.join(map(str, kline))
        # message['stock'] = stock

        for i in range(1, page + 1):
            status = xueqiu.search_status(cookie, symbol, i, count, source)
            message = {**message, **status}
        for key, value in message.items():
            if 'replyCount' in value and value['replyCount'] > 0:
                comment = xueqiu.search_comments(cookie, key)
                value['comment'] = comment
                time.sleep(random.random() * 5)
        xueqiu.export_text(list(message.values()), symbol, symbol, True)

        last_message = ''
        if session_id:
            last_message = RedisService.get_hset(f'{user_id}:message', session_id)
        
        prompt = f'量化市场情绪指标，判断{stock['name']}股票近两天涨跌，给出购买价格\n{last_message}'
        pattern = re.compile(rf'{symbol}-\d+')
        directory = f'libs/xueqiu/data/{symbol}/'
        file_ids = []
        for filename in os.listdir(directory):
            if pattern.search(filename):
                symbol_path = os.path.join(directory, filename)
                encoder = freeAI.process_local_file(symbol_path)
                file_id = freeAI.upload_file(encoder, token)
                file_ids.append(file_id)
            
        if len(file_ids) == 0 or freeAI.fetch_files(file_ids, token):
            new_session_id = freeAI.create_session(token)
            result, message_id = freeAI.completion(prompt, file_ids, new_session_id, None, token)
            RedisService.update_hset(f'{user_id}:session', new_session_id, message_id)
            
        return {
            'status': 'success',
            'session_id': session_id,
            'result': result
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }
    

@xueqiu_bp.route('/recommend_gn_hy_stock', methods=['GET'])
def recommend_gn_hy_stock():
    user_id = request.args.get('userId')
    code = request.args.get('code')
    cookie = RedisService.get_cookie(user_id)
    token = RedisService.get_hset(f'user:{user_id}', 'token')
    if not cookie or not token:
        return {
            'status': 'error',
            'message': 'Please login first.'
        }
    
    now = datetime.now().replace(microsecond=0)
    timestamp_ms = int(now.timestamp() * 1000)
    
    try:
        name = ''
        zj_stocks = []
        if code in jqka.gn_mapping:
            name = jqka.gn_mapping[code]
            zj_stocks = jqka.search_gnzj(code, 5)
        elif code in jqka.hy_mapping:
            name = jqka.hy_mapping[code]
            zj_stocks = jqka.search_hyzj(code, 5)
        else:
            return {
                'status': 'error',
                'message': 'code not exit.'
            }
        
        stocks = []
        for zj_stock in zj_stocks:
            symbol = xueqiu.search_stock_by_name(cookie, zj_stock['name'])
            if xueqiu.is_gem_or_star_stock(symbol):
                continue

            stock = xueqiu.search_stock(cookie, symbol)
            zj_stock['symbol'] = symbol
            zj_stock['volume'] = stock['volume']
            if stock['exchange'] == 'SZ' or stock['exchange'] == 'SH':
                # kline = xueqiu.search_kline(cookie, symbol, timestamp_ms, -100)
                # zj_stock['kline'] = ','.join(map(str, kline))
                # stocks.append(zj_stock)
                robot_data = jqka.search_robot_data(zj_stock['name'])
                new_stock = {**zj_stock, **robot_data}
                stocks.append(new_stock)
                time.sleep(random.random() * 10)
        
        if len(stocks) == 0:
            return {
                'status': 'error',
                'message': 'stock not exit.'
            }

        jqka.export_text(stocks, '', name)

        prompt = f'分析今天的{name}股票走向，推荐近两天会涨、今天值得购买的股票，给出购买价格'
        encoder = freeAI.process_local_file(f'libs/jqka/data/{name}.txt')
        file_id = freeAI.upload_file(encoder, token)
        if freeAI.fetch_files([file_id], token):
            session_id = freeAI.create_session(token)
            result, message_id = freeAI.completion(prompt, [file_id], session_id, None, token)
            RedisService.update_hset(f'{user_id}:session', session_id, message_id)
            # RedisService.update_hset(f'{user_id}:message', session_id, result)
        
        return {
            'status': 'success',
            'session_id': session_id,
            'result': result
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }