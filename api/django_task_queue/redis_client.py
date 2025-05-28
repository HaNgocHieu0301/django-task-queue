import redis
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Redis client wrapper để quản lý kết nối Redis
    """
    _instance = None
    _connection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._connection is None:
            self._connection = self._create_connection()

    def _create_connection(self):
        """
        Tạo kết nối Redis với cấu hình từ settings
        """
        try:
            connection = redis.Redis(
                host=settings.REDIS_HOST,
                port=int(settings.REDIS_PORT),
                db=int(settings.REDIS_DB),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            connection.ping()
            logger.info(f"Redis connection established successfully to {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            return connection
            
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {e}")
            raise

    def get_connection(self):
        """
        Lấy Redis connection instance
        """
        if self._connection is None:
            self._connection = self._create_connection()
        return self._connection

    def ping(self):
        """
        Kiểm tra kết nối Redis
        """
        try:
            return self._connection.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False

    def set(self, key, value, ex=None):
        """
        Set key-value trong Redis
        """
        try:
            return self._connection.set(key, value, ex=ex)
        except Exception as e:
            logger.error(f"Redis set failed: {e}")
            return False

    def get(self, key):
        """
        Get value từ Redis
        """
        try:
            return self._connection.get(key)
        except Exception as e:
            logger.error(f"Redis get failed: {e}")
            return None

    def delete(self, key):
        """
        Xóa key từ Redis
        """
        try:
            return self._connection.delete(key)
        except Exception as e:
            logger.error(f"Redis delete failed: {e}")
            return False

    def close(self):
        """
        Đóng kết nối Redis
        """
        if self._connection:
            self._connection.close()
            self._connection = None


# Singleton instance
redis_client = RedisClient() 