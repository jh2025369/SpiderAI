from flask import Blueprint, request
import time
from libs.xueqiu.module import request_xueqiu, search_status, search_comments, export_text
from services.redis_service import RedisService

xueqiu_bp = Blueprint('xueqiu', __name__)

@xueqiu_bp.route('/get_cookie', methods=['GET'])
def get_cookie():
    user_id = request.args.get('userId')
    cookie = request_xueqiu()
    RedisService.set_cookie(user_id, cookie)
    return {
        'status': 'success',
        'cookie': cookie
    }


@xueqiu_bp.route('/search_status', methods=['GET'])
def search_status():
    userId = request.args.get('userId')
    symbol = request.args.get('symbol')
    count = request.args.get('count')
    cookie = RedisService.get_cookie(userId)
    if not cookie:
        return {
            'status': 'error',
            'message': 'Please login first.'
        }
    
    try:
        message = search_status(symbol, count, cookie)
        for key, value in message.items():
            comment = search_comments(key, cookie)
            value['comment'] = comment
            time.sleep(5)
        export_text(message, symbol)
        return {
            'status': 'success',
            'items': message
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }
