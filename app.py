from flask import Flask
from config import Config
from services.redis_service import RedisService
from controller.miaoshou_controller import miaoshou_bp
from controller.free_ai_controller import free_ai_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    RedisService.init_redis(app.config)

    app.register_blueprint(miaoshou_bp, url_prefix='/miaoshou')
    app.register_blueprint(free_ai_bp, url_prefix='/freeAI')

    return app

app = create_app()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)