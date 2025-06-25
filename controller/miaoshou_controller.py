from flask import Blueprint, request
from libs.miaoshou.module import login, get_account_shop_list, searchItemList
from services.redis_service import RedisService

miaoshou_bp = Blueprint('miaoshou', __name__)

@miaoshou_bp.route('/login', methods=['GET'])
def request_login():
    username = request.args.get('username')
    password = request.args.get('password')
    cookie = login(username, password)
    RedisService.set_cookie(username, cookie)
    return {
        'status': 'success',
        'cookie': cookie
    }


@miaoshou_bp.route('/search_item_list', methods=['GET'])
def search_item_list():
    userId = request.args.get('userId')
    pageNo = request.args.get('pageNo')
    pageSize = request.args.get('pageSize')
    cookie = RedisService.get_cookie(userId)
    if not cookie:
        return {
            'status': 'error',
            'message': 'Please login first.'
        }
    
    try:
        shopIds = get_account_shop_list(cookie)
        itemList = searchItemList(shopIds, pageNo, pageSize, cookie)
        return {
            'status': 'success',
            'items': itemList
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }
