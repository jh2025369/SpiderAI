from redis import Redis
from datetime import timedelta
from config import Config

class RedisService:
    _conn = None

    @classmethod
    def init_redis(cls, app_config):
        """初始化Redis连接"""
        cls._conn = Redis(
            host=app_config['REDIS_HOST'],
            port=app_config['REDIS_PORT'],
            db=app_config['REDIS_DB'],
            password=app_config['REDIS_PASSWORD'],
            decode_responses=True,
            socket_connect_timeout=3  # 连接超时设置
        )
        try:
            cls._conn.ping()  # 测试连接
            print("Redis连接成功")
        except Exception as e:
            print(f"Redis连接失败: {str(e)}")
            raise

    @classmethod
    def set_cookie(cls, user_id, cookie):
        """存储Cookie并设置过期"""
        if not cls._conn:
            raise RuntimeError("Redis未初始化")
        cls._conn.setex(
            name=f"user:{user_id}:cookie",
            time=timedelta(seconds=Config.SESSION_EXPIRE),
            value=cookie
        )
    
    @classmethod
    def get_cookie(cls, user_id):
        """获取Cookie"""
        if not cls._conn:
            raise RuntimeError("Redis未初始化")
        return cls._conn.get(f"user:{user_id}:cookie")
    
    @classmethod
    def delete_cookie(cls, user_id):
        """删除Cookie"""
        if not cls._conn:
            raise RuntimeError("Redis未初始化")
        cls._conn.delete(f"user:{user_id}:cookie")

    @classmethod
    def get_connection(cls):
        """获取原始连接（用于特殊操作）"""
        return cls._conn