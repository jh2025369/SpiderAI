from flask import Blueprint, request
from libs.miaoshou.module import login, get_account_shop_list, searchItemList

miaoshou_bp = Blueprint('miaoshou', __name__)

cookie = ''

@miaoshou_bp.route('/login', methods=['GET'])
def request_login():
    global cookie
    username = request.args.get('username')
    password = request.args.get('password')
    cookie = login(username, password)
    return {
        'status': 'success',
        'cookie': cookie
    }


@miaoshou_bp.route('/search_item_list', methods=['GET'])
def search_item_list():
    global cookie
    if not cookie:
        return {
            'status': 'error',
            'message': 'Please login first.'
        }
    
    try:
        shopIds = get_account_shop_list(cookie)
        itemList = searchItemList(shopIds, cookie)
        return {
            'status': 'success',
            'items': itemList
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }
