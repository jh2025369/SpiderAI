from flask import Blueprint, request
from requests_toolbelt import MultipartEncoder
from libs.freeAI.module import get_device_id, login, upload_file, create_session, fetch_files, completion
from libs.freeAI.module import process_image_url, process_local_file
from services.redis_service import RedisService

free_ai_bp = Blueprint('freeAI', __name__)

@free_ai_bp.route('/login', methods=['GET'])
def request_login():
    user_id = request.args.get('userId')
    mobile = request.args.get('mobile')
    password = request.args.get('password')
    device_id = request.args.get('deviceId')
    if not device_id:
        device_id = get_device_id()
    token = login(mobile, password, device_id)
    RedisService.set_hset(f'user:{user_id}', {
        'token': token,
        'deviceId': device_id
    })
    return {
        'status': 'success',
        'token': token,
        'deviceId': device_id
    }


@free_ai_bp.route('/chat', methods=['post'])
def chat():
    user_id = request.form.get('userId')
    images = request.form.get('images', [])
    prompt = request.form.get('prompt')
    session_id = request.form.get('sessionId')
    token = request.form.get('token')
    files = request.files.getlist('files')
    if not token:
        token = RedisService.get_hset(f'user:{user_id}', 'token')
    if not token:
        return {
            'status': 'error',
            'message': 'Please login first.'
        }
    
    try:
        file_ids = []
        for imageUrl in images:
            encoder = process_image_url(imageUrl)
            file_id = upload_file(encoder, token)
            file_ids.append(file_id)
        
        for file in files:
            encoder = MultipartEncoder(
                fields={
                    'file': (file.filename, file.stream, file.mimetype)
                }
            )
            file_id = upload_file(encoder, token)
            file_ids.append(file_id)
        
        
        if len(file_ids) == 0 or fetch_files(file_ids, token):
            parent_message_id = None
            if session_id:
                parent_message_id = int(RedisService.get_hset(f'{user_id}:session', session_id))
            else:
                session_id = create_session(token)
            result, message_id = completion(prompt, file_ids, session_id, parent_message_id, token)
            RedisService.update_hset(f'{user_id}:session', session_id, message_id)
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
