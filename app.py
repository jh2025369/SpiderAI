from flask import Flask
from config import Config
from services.redis_service import RedisService
from routes.miaoshou_routes import miaoshou_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    RedisService.init_redis(app.config)

    app.register_blueprint(miaoshou_bp, url_prefix='/miaoshou')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8080, debug=True)