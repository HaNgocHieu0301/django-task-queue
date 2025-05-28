import pytest
import json
import time
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from tasks.models import Task, TaskStatus, TaskPriority
from django_task_queue.queue_manager import QueueManager
from django_task_queue.redis_client import redis_client


class TestQueueManager(TestCase):
    """Test cases cho QueueManager"""
    
    def setUp(self):
        """Setup trước mỗi test"""
        self.queue_manager = QueueManager(queue_name="test_queue")
        self.redis = redis_client.get_connection()
        self._clear_test_queues()
    
    def tearDown(self):
        """Cleanup sau mỗi test"""
        self._clear_test_queues()
    
    def _clear_test_queues(self):
        """Helper method để clear test queues"""
        # Clear all queue keys
        keys_pattern = [
            "task_queue:pending:test_queue",
            "task_queue:processing:*",
            "task_queue:completed:test_queue",
            "task_queue:retry",
            "task_queue:dead_letter"
        ]
        
        for pattern in keys_pattern:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
        
        # Clear all test tasks from database
        Task.objects.filter(queue_name="test_queue").delete()
    
    def test_enqueue_task_success(self):
        """Test thêm task vào queue thành công"""
        task_id = self.queue_manager.enqueue_task(
            task_name="test_function",
            args=("arg1", "arg2"),
            kwargs={"key": "value"},
            priority=TaskPriority.HIGH,
            max_retries=5,
            retry_delay=120
        )
        
        # Kiểm tra task được tạo trong database
        self.assertIsNotNone(task_id)
        task = Task.objects.get(id=task_id)
        self.assertEqual(task.task_name, "test_function")
        self.assertEqual(task.args, ["arg1", "arg2"])
        self.assertEqual(task.kwargs, {"key": "value"})
        self.assertEqual(task.priority, 3)  # TaskPriority.HIGH = 3
        self.assertEqual(task.max_retries, 5)
        self.assertEqual(task.retry_delay, 120)
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.queue_name, "test_queue")
        
        # Kiểm tra task được thêm vào Redis queue
        queue_key = f"{self.queue_manager.PENDING_QUEUE}:test_queue"
        queue_size = self.redis.zcard(queue_key)
        self.assertEqual(queue_size, 1)
    
    def test_enqueue_task_with_defaults(self):
        """Test thêm task với các giá trị mặc định"""
        task_id = self.queue_manager.enqueue_task(task_name="simple_task")
        
        task = Task.objects.get(id=task_id)
        self.assertEqual(task.args, [])
        self.assertEqual(task.kwargs, {})
        self.assertEqual(task.priority, 2)  # TaskPriority.NORMAL = 2
        self.assertEqual(task.max_retries, 3)
        self.assertEqual(task.retry_delay, 60)
    
    def test_dequeue_task_success(self):
        """Test lấy task từ queue thành công"""
        # Thêm task vào queue
        task_id = self.queue_manager.enqueue_task(
            task_name="test_function",
            args=["arg1"],
            priority=TaskPriority.HIGH
        )
        
        # Lấy task từ queue
        worker_id = "test_worker_123"
        task_data = self.queue_manager.dequeue_task(worker_id)
        
        self.assertIsNotNone(task_data)
        self.assertEqual(task_data["task_id"], task_id)
        self.assertEqual(task_data["task_name"], "test_function")
        self.assertEqual(task_data["worker_id"], worker_id)
        self.assertIn("started_at", task_data)
        
        # Kiểm tra task status trong database
        task = Task.objects.get(id=task_id)
        self.assertEqual(task.status, TaskStatus.PROCESSING)
        self.assertEqual(task.worker_id, worker_id)
        self.assertIsNotNone(task.started_at)
        
        # Kiểm tra task đã được move từ pending queue
        queue_key = f"{self.queue_manager.PENDING_QUEUE}:test_queue"
        queue_size = self.redis.zcard(queue_key)
        self.assertEqual(queue_size, 0)
    
    def test_dequeue_task_empty_queue(self):
        """Test lấy task từ queue rỗng"""
        worker_id = "test_worker_123"
        task_data = self.queue_manager.dequeue_task(worker_id)
        
        self.assertIsNone(task_data)
    
    def test_dequeue_task_priority_order(self):
        """Test lấy task theo thứ tự priority"""
        # Thêm tasks với priority khác nhau
        low_task_id = self.queue_manager.enqueue_task(
            task_name="low_task", priority=TaskPriority.LOW
        )
        high_task_id = self.queue_manager.enqueue_task(
            task_name="high_task", priority=TaskPriority.HIGH
        )
        normal_task_id = self.queue_manager.enqueue_task(
            task_name="normal_task", priority=TaskPriority.NORMAL
        )
        critical_task_id = self.queue_manager.enqueue_task(
            task_name="critical_task", priority=TaskPriority.CRITICAL
        )
        
        worker_id = "test_worker"
        
        # Lấy tasks - should be in priority order: CRITICAL, HIGH, NORMAL, LOW
        task1 = self.queue_manager.dequeue_task(worker_id + "_1")
        self.assertEqual(task1["task_id"], critical_task_id)
        
        task2 = self.queue_manager.dequeue_task(worker_id + "_2")
        self.assertEqual(task2["task_id"], high_task_id)
        
        task3 = self.queue_manager.dequeue_task(worker_id + "_3")
        self.assertEqual(task3["task_id"], normal_task_id)
        
        task4 = self.queue_manager.dequeue_task(worker_id + "_4")
        self.assertEqual(task4["task_id"], low_task_id)
    
    def test_complete_task_success(self):
        """Test hoàn thành task thành công"""
        # Thêm và lấy task
        task_id = self.queue_manager.enqueue_task(task_name="test_function")
        worker_id = "test_worker"
        task_data = self.queue_manager.dequeue_task(worker_id)
        
        # Complete task
        result = {"success": True, "data": "test_result"}
        success = self.queue_manager.complete_task(task_id, worker_id, result)
        
        self.assertTrue(success)
        
        # Kiểm tra task status trong database
        task = Task.objects.get(id=task_id)
        self.assertEqual(task.status, TaskStatus.SUCCESS)
        self.assertEqual(task.result, result)
        self.assertIsNotNone(task.completed_at)
        
        # Kiểm tra task đã được thêm vào completed queue
        completed_key = f"{self.queue_manager.COMPLETED_QUEUE}:test_queue"
        completed_tasks = self.redis.lrange(completed_key, 0, -1)
        self.assertIn(task_id, [task.decode() if isinstance(task, bytes) else task for task in completed_tasks])
    
    def test_fail_task_with_retry(self):
        """Test task thất bại và được retry"""
        # Thêm task với max_retries > 0
        task_id = self.queue_manager.enqueue_task(
            task_name="test_function",
            max_retries=2,
            retry_delay=1
        )
        
        # Lấy task
        worker_id = "test_worker"
        task_data = self.queue_manager.dequeue_task(worker_id)
        
        # Fail task
        error_message = "Test error"
        success = self.queue_manager.fail_task(task_id, worker_id, error_message)
        
        self.assertTrue(success)
        
        # Kiểm tra task được đánh dấu retry
        task = Task.objects.get(id=task_id)
        self.assertEqual(task.status, TaskStatus.RETRY)
        self.assertEqual(task.retry_count, 1)
        self.assertIsNotNone(task.next_retry_at)
        
        # Kiểm tra task được thêm vào retry queue
        retry_tasks = self.redis.zrange(self.queue_manager.RETRY_QUEUE, 0, -1)
        self.assertEqual(len(retry_tasks), 1)
    
    def test_fail_task_max_retries_exceeded(self):
        """Test task thất bại khi đã hết retry"""
        # Tạo task đã retry max lần
        task = Task.objects.create(
            task_name="test_function",
            queue_name="test_queue",
            retry_count=3,
            max_retries=3
        )
        
        # Fail task
        worker_id = "test_worker"
        error_message = "Final error"
        success = self.queue_manager.fail_task(str(task.id), worker_id, error_message)
        
        self.assertTrue(success)
        
        # Kiểm tra task được đánh dấu failed
        task.refresh_from_db()
        self.assertEqual(task.status, TaskStatus.FAILED)
        self.assertEqual(task.error_message, error_message)
        
        # Kiểm tra task được thêm vào dead letter queue
        dead_tasks = self.redis.lrange(self.queue_manager.DEAD_LETTER_QUEUE, 0, -1)
        self.assertEqual(len(dead_tasks), 1)
    
    def test_process_retry_queue(self):
        """Test xử lý retry queue"""
        # Tạo task cần retry
        task = Task.objects.create(
            task_name="test_function",
            queue_name="test_queue",
            status=TaskStatus.RETRY,
            retry_count=1,
            next_retry_at=timezone.now() - timedelta(seconds=1)  # Past time
        )
        
        # Thêm task vào retry queue
        retry_data = task.to_dict()
        retry_score = (timezone.now() - timedelta(seconds=1)).timestamp()
        self.redis.zadd(self.queue_manager.RETRY_QUEUE, {json.dumps(retry_data): retry_score})
        
        # Process retry queue
        self.queue_manager.process_retry_queue()
        
        # Kiểm tra task đã được move về pending
        task.refresh_from_db()
        self.assertEqual(task.status, TaskStatus.PENDING)
        
        # Kiểm tra task đã được thêm vào pending queue
        queue_key = f"{self.queue_manager.PENDING_QUEUE}:test_queue"
        queue_size = self.redis.zcard(queue_key)
        self.assertEqual(queue_size, 1)
        
        # Kiểm tra retry queue đã empty
        retry_size = self.redis.zcard(self.queue_manager.RETRY_QUEUE)
        self.assertEqual(retry_size, 0)
    
    def test_get_queue_stats(self):
        """Test lấy thống kê queue"""
        # Thêm một số tasks
        task1_id = self.queue_manager.enqueue_task("task1", priority=TaskPriority.HIGH)
        task2_id = self.queue_manager.enqueue_task("task2", priority=TaskPriority.LOW)
        
        # Lấy một task để processing
        worker_id = "test_worker"
        self.queue_manager.dequeue_task(worker_id)
        
        # Complete một task
        self.queue_manager.complete_task(task2_id, worker_id, "result")
        
        stats = self.queue_manager.get_queue_stats()
        
        self.assertEqual(stats["pending"], 1)  # task1 still pending
        self.assertEqual(stats["completed"], 1)  # task2 completed
        # Note: processing count might be 0 due to implementation details
    
    @patch('django_task_queue.queue_manager.logger')
    def test_enqueue_task_redis_error(self, mock_logger):
        """Test xử lý lỗi Redis khi enqueue task"""
        with patch.object(self.redis, 'zadd', side_effect=Exception("Redis error")):
            with self.assertRaises(Exception):
                self.queue_manager.enqueue_task(task_name="test_function")
            
            mock_logger.error.assert_called()
    
    def test_dequeue_task_with_auto_worker_id(self):
        """Test dequeue task với worker_id tự động"""
        task_id = self.queue_manager.enqueue_task(task_name="test_function")
        
        # Dequeue without worker_id
        task_data = self.queue_manager.dequeue_task("")
        
        self.assertIsNotNone(task_data)
        self.assertIn("worker_", task_data["worker_id"])
        self.assertEqual(task_data["task_id"], task_id) 