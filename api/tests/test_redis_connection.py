import redis
import time
from django.test import TestCase
from django.conf import settings
from django_task_queue.redis_client import redis_client


class TestRedisConnection(TestCase):
    """
    Test cases to test Redis connection and basic functions
    """

    def setUp(self):
        """
        Test setup before each test case
        """
        self.redis_client = redis_client
        self.test_key = "test_key_django_worker"
        self.test_value = "test_value_123"

    def tearDown(self):
        """
        Test cleanup after each test case
        """
        # Test delete test keys
        try:
            self.redis_client.delete(self.test_key)
            self.redis_client.delete(f"{self.test_key}_expire")
        except:
            pass

    def test_redis_connection_successful(self):
        """
        Test: Test Redis connection successful
        """
        # Test ping
        result = self.redis_client.ping()
        self.assertTrue(result, "Redis connection should be successful")

    def test_redis_connection_parameters(self):
        """
        Test: Test Redis connection parameters
        """
        connection = self.redis_client.get_connection()

        # Test connection is not None
        self.assertIsNotNone(connection, "Redis connection should not be None")

        # Test connection is Redis instance
        self.assertIsInstance(
            connection, redis.Redis, "Connection should be Redis instance"
        )

    def test_redis_set_and_get(self):
        """
        Test: Test Redis set and get
        """
        # Test set
        set_result = self.redis_client.set(self.test_key, self.test_value)
        self.assertTrue(set_result, "Redis set should be successful")

        # Test get
        get_result = self.redis_client.get(self.test_key)
        self.assertEqual(
            get_result, self.test_value, "Redis get should return correct value"
        )

    def test_redis_set_with_expiration(self):
        """
        Test: Test Redis set with expiration
        """
        expire_key = f"{self.test_key}_expire"
        expire_time = 2  # 2 seconds

        # Test set with expiration
        set_result = self.redis_client.set(expire_key, self.test_value, ex=expire_time)
        self.assertTrue(set_result, "Redis set with expiration should be successful")

        # Test value immediately
        get_result = self.redis_client.get(expire_key)
        self.assertEqual(get_result, self.test_value, "Value should exist immediately")

        # Test expiration
        time.sleep(expire_time + 1)

        # Test value expired
        expired_result = self.redis_client.get(expire_key)
        self.assertIsNone(expired_result, "Value should be expired")

    def test_redis_delete(self):
        """
        Test: Test Redis delete
        """
        # Test set value
        self.redis_client.set(self.test_key, self.test_value)

        # Test value exists
        get_result = self.redis_client.get(self.test_key)
        self.assertEqual(
            get_result, self.test_value, "Value should exist before delete"
        )

        # Test delete
        delete_result = self.redis_client.delete(self.test_key)
        self.assertTrue(delete_result, "Redis delete should be successful")

        # Test value after delete
        get_after_delete = self.redis_client.get(self.test_key)
        self.assertIsNone(get_after_delete, "Value should not exist after delete")

    def test_redis_connection_settings(self):
        """
        Test: Test Redis connection settings
        """
        # Test settings
        self.assertIsNotNone(settings.REDIS_HOST, "REDIS_HOST should be configured")
        self.assertIsNotNone(settings.REDIS_PORT, "REDIS_PORT should be configured")
        self.assertIsNotNone(settings.REDIS_DB, "REDIS_DB should be configured")

        # Test default values
        self.assertIn(
            settings.REDIS_HOST, ["localhost", "redis"], "REDIS_HOST should be valid"
        )
        self.assertEqual(int(settings.REDIS_PORT), 6379, "REDIS_PORT should be 6379")
        self.assertEqual(int(settings.REDIS_DB), 0, "REDIS_DB should be 0")
