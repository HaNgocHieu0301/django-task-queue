import pytest
import redis
import time
from django.test import TestCase
from django.conf import settings
from django_task_queue.redis_client import RedisClient, redis_client


class TestRedisConnection(TestCase):
    """
    Test cases để kiểm tra kết nối Redis và các chức năng cơ bản
    """

    def setUp(self):
        """
        Setup trước mỗi test case
        """
        self.redis_client = redis_client
        self.test_key = "test_key_django_worker"
        self.test_value = "test_value_123"

    def tearDown(self):
        """
        Cleanup sau mỗi test case
        """
        # Xóa test keys
        try:
            self.redis_client.delete(self.test_key)
            self.redis_client.delete(f"{self.test_key}_expire")
        except:
            pass

    def test_redis_connection_successful(self):
        """
        Test: Kiểm tra kết nối Redis thành công
        """
        # Test ping
        result = self.redis_client.ping()
        self.assertTrue(result, "Redis connection should be successful")

    def test_redis_connection_parameters(self):
        """
        Test: Kiểm tra các tham số kết nối Redis
        """
        connection = self.redis_client.get_connection()
        
        # Kiểm tra connection không None
        self.assertIsNotNone(connection, "Redis connection should not be None")
        
        # Kiểm tra connection là Redis instance
        self.assertIsInstance(connection, redis.Redis, "Connection should be Redis instance")

    def test_redis_set_and_get(self):
        """
        Test: Kiểm tra chức năng set và get
        """
        # Test set
        set_result = self.redis_client.set(self.test_key, self.test_value)
        self.assertTrue(set_result, "Redis set should be successful")
        
        # Test get
        get_result = self.redis_client.get(self.test_key)
        self.assertEqual(get_result, self.test_value, "Redis get should return correct value")

    def test_redis_set_with_expiration(self):
        """
        Test: Kiểm tra set với thời gian hết hạn
        """
        expire_key = f"{self.test_key}_expire"
        expire_time = 2  # 2 seconds
        
        # Set với expiration
        set_result = self.redis_client.set(expire_key, self.test_value, ex=expire_time)
        self.assertTrue(set_result, "Redis set with expiration should be successful")
        
        # Kiểm tra value ngay lập tức
        get_result = self.redis_client.get(expire_key)
        self.assertEqual(get_result, self.test_value, "Value should exist immediately")
        
        # Đợi hết hạn
        time.sleep(expire_time + 1)
        
        # Kiểm tra value đã hết hạn
        expired_result = self.redis_client.get(expire_key)
        self.assertIsNone(expired_result, "Value should be expired")

    def test_redis_delete(self):
        """
        Test: Kiểm tra chức năng delete
        """
        # Set value trước
        self.redis_client.set(self.test_key, self.test_value)
        
        # Kiểm tra value tồn tại
        get_result = self.redis_client.get(self.test_key)
        self.assertEqual(get_result, self.test_value, "Value should exist before delete")
        
        # Delete
        delete_result = self.redis_client.delete(self.test_key)
        self.assertTrue(delete_result, "Redis delete should be successful")
        
        # Kiểm tra value đã bị xóa
        get_after_delete = self.redis_client.get(self.test_key)
        self.assertIsNone(get_after_delete, "Value should not exist after delete")

    def test_redis_connection_settings(self):
        """
        Test: Kiểm tra cấu hình Redis từ settings
        """
        # Kiểm tra settings có đúng không
        self.assertIsNotNone(settings.REDIS_HOST, "REDIS_HOST should be configured")
        self.assertIsNotNone(settings.REDIS_PORT, "REDIS_PORT should be configured")
        self.assertIsNotNone(settings.REDIS_DB, "REDIS_DB should be configured")
        
        # Kiểm tra giá trị mặc định
        self.assertIn(settings.REDIS_HOST, ['localhost', 'redis'], "REDIS_HOST should be valid")
        self.assertEqual(int(settings.REDIS_PORT), 6379, "REDIS_PORT should be 6379")
        self.assertEqual(int(settings.REDIS_DB), 0, "REDIS_DB should be 0")


@pytest.mark.django_db
class TestRedisConnectionPytest:
    """
    Test cases sử dụng pytest để kiểm tra Redis connection
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        """
        Setup cho pytest
        """
        self.redis_client = redis_client
        self.test_key = "pytest_test_key"
        self.test_value = "pytest_test_value"
        
        yield
        
        # Cleanup
        try:
            self.redis_client.delete(self.test_key)
        except:
            pass

    def test_redis_ping_success(self):
        """
        Test: Redis ping thành công
        """
        result = self.redis_client.ping()
        assert result is True, "Redis ping should return True"

    def test_redis_basic_operations(self):
        """
        Test: Các thao tác cơ bản với Redis
        """
        # Set
        set_result = self.redis_client.set(self.test_key, self.test_value)
        assert set_result is True, "Set operation should succeed"
        
        # Get
        get_result = self.redis_client.get(self.test_key)
        assert get_result == self.test_value, "Get should return correct value"
        
        # Delete
        delete_result = self.redis_client.delete(self.test_key)
        assert delete_result > 0, "Delete should return number of deleted keys"
        
        # Verify deletion
        get_after_delete = self.redis_client.get(self.test_key)
        assert get_after_delete is None, "Key should not exist after deletion"

    def test_redis_connection_error_handling(self):
        """
        Test: Xử lý lỗi kết nối Redis
        """
        # Test với key không tồn tại
        non_existent_value = self.redis_client.get("non_existent_key_12345")
        assert non_existent_value is None, "Non-existent key should return None"


class TestRedisConnectionIntegration(TestCase):
    """
    Integration tests cho Redis connection
    """

    def test_redis_connection_in_docker_environment(self):
        """
        Test: Kiểm tra kết nối Redis trong môi trường Docker
        """
        # Kiểm tra environment variables
        import os
        
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = os.getenv('REDIS_PORT', '6379')
        redis_db = os.getenv('REDIS_DB', '0')
        
        # Test connection với environment variables
        try:
            test_connection = redis.Redis(
                host=redis_host,
                port=int(redis_port),
                db=int(redis_db),
                socket_connect_timeout=5
            )
            
            ping_result = test_connection.ping()
            self.assertTrue(ping_result, "Redis should be accessible in Docker environment")
            
        except redis.ConnectionError:
            self.fail("Redis connection failed in Docker environment")

    def test_redis_singleton_pattern(self):
        """
        Test: Kiểm tra Singleton pattern của RedisClient
        """
        client1 = RedisClient()
        client2 = RedisClient()
        
        # Cả hai instance phải giống nhau
        self.assertIs(client1, client2, "RedisClient should follow Singleton pattern")
        
        # Connection cũng phải giống nhau
        conn1 = client1.get_connection()
        conn2 = client2.get_connection()
        self.assertIs(conn1, conn2, "Redis connections should be the same instance") 