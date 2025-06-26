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
    def set_value(cls, key, value, expire=None):
        if expire:
            return cls._conn.setex(key, expire, value)
        return cls._conn.set(key, value)
    
    @classmethod
    def get_value(cls, key):
        return cls._conn.get(key)
    
    @classmethod
    def delete_key(cls, key):
        return cls._conn.delete(key)

    @classmethod
    def set_hset(cls, key, mapping):
        cls._conn.delete(key)
        return cls._conn.hmset(key, mapping=mapping)
    
    @classmethod
    def update_hset(cls, key, field, value):
        return cls._conn.hset(key, field, value)
    
    @classmethod
    def get_hset(cls, key, field=None):
        if field:
            return cls._conn.hget(key, field)
        else:
            return cls._conn.hgetall(key)
    
    @classmethod
    def delete_hset(cls, key, *fields):
        if not fields:
            return cls._conn.delete(key)
        return cls._conn.hdel(key, *fields)

    @classmethod
    def set_cookie(cls, user_id, cookie):
        """存储Cookie并设置过期"""
        if not cls._conn:
            raise RuntimeError("Redis未初始化")
        return cls._conn.setex(
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
        return cls._conn.delete(f"user:{user_id}:cookie")

    @classmethod
    def get_connection(cls):
        """获取原始连接（用于特殊操作）"""
        return cls._conn