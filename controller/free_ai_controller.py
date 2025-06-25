from flask import Blueprint, request
from libs.freeAI.module import get_device_id, login, upload_file, create_session, fetch_files, completion
from services.redis_service import RedisService

free_ai_bp = Blueprint('freeAI', __name__)

@free_ai_bp.route('/login', methods=['GET'])
def request_login():
    userId = request.args.get('userId')
    mobile = request.args.get('mobile')
    password = request.args.get('password')
    device_id = request.args.get('deviceId')
    if not device_id:
        device_id = get_device_id()
    token = login(mobile, password, device_id)
    RedisService.set_hset(userId, {
        'token': token,
        'device_id': device_id
    })
    return {
        'status': 'success',
        'token': token,
        'device_id': device_id
    }


@free_ai_bp.route('/validate_image', methods=['post'])
def validate_image():
    json_data = request.get_json()
    userId = json_data.get('userId')
    images = json_data.get('images')
    prompt = json_data.get('prompt')
    session_id = json_data.get('sessionId')
    token = json_data.get('token')
    if not token:
        token = RedisService.get_hset(userId, 'token')
    if not token:
        return {
            'status': 'error',
            'message': 'Please login first.'
        }
    
    try:
        file_ids = []
        for imageUrl in images:
            file_id = upload_file(imageUrl, token)
            file_ids.append(file_id)
        
        if fetch_files(file_ids, token):
            parent_message_id = None
            if session_id:
                parent_message_id = RedisService.get_value(session_id)
            else:
                session_id = create_session(token)
            result, message_id = completion(prompt, file_ids, session_id, parent_message_id, token)
            RedisService.set_value(session_id, message_id)
            return {
                'status': 'success',
                'sessionId': session_id,
                'message': result
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }
