import pytest
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from tasks.models import Task, TaskStatus, TaskPriority, TaskLog


class TestTaskModel(TestCase):
    """Test cases cho Task model"""
    
    def setUp(self):
        """Setup trước mỗi test"""
        self.task_data = {
            'task_name': 'test_task',
            'args': ['arg1', 'arg2'],
            'kwargs': {'key': 'value'},
            'priority': TaskPriority.NORMAL,
            'max_retries': 3,
            'retry_delay': 60,
            'queue_name': 'test_queue'
        }
    
    def test_create_task(self):
        """Test tạo task mới"""
        task = Task.objects.create(**self.task_data)
        
        self.assertIsNotNone(task.id)
        self.assertEqual(task.task_name, 'test_task')
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.priority, TaskPriority.NORMAL)
        self.assertEqual(task.args, ['arg1', 'arg2'])
        self.assertEqual(task.kwargs, {'key': 'value'})
        self.assertEqual(task.retry_count, 0)
        self.assertIsNotNone(task.created_at)
        self.assertIsNone(task.started_at)
        self.assertIsNone(task.completed_at)
    
    def test_task_to_dict(self):
        """Test chuyển task thành dictionary"""
        task = Task.objects.create(**self.task_data)
        task_dict = task.to_dict()
        
        self.assertEqual(task_dict['task_id'], str(task.id))
        self.assertEqual(task_dict['task_name'], 'test_task')
        self.assertEqual(task_dict['args'], ['arg1', 'arg2'])
        self.assertEqual(task_dict['kwargs'], {'key': 'value'})
        self.assertEqual(task_dict['priority'], TaskPriority.NORMAL)
        self.assertEqual(task_dict['queue_name'], 'test_queue')
    
    def test_mark_as_processing(self):
        """Test đánh dấu task đang xử lý"""
        task = Task.objects.create(**self.task_data)
        worker_id = 'worker_123'
        
        task.mark_as_processing(worker_id)
        
        self.assertEqual(task.status, TaskStatus.PROCESSING)
        self.assertEqual(task.worker_id, worker_id)
        self.assertIsNotNone(task.started_at)
    
    def test_mark_as_completed(self):
        """Test đánh dấu task hoàn thành"""
        task = Task.objects.create(**self.task_data)
        result = {'success': True, 'data': 'test_result'}
        
        task.mark_as_completed(result)
        
        self.assertEqual(task.status, TaskStatus.SUCCESS)
        self.assertEqual(task.result, result)
        self.assertIsNotNone(task.completed_at)
    
    def test_mark_as_failed(self):
        """Test đánh dấu task thất bại"""
        task = Task.objects.create(**self.task_data)
        error_message = 'Test error message'
        
        task.mark_as_failed(error_message)
        
        self.assertEqual(task.status, TaskStatus.FAILED)
        self.assertEqual(task.error_message, error_message)
        self.assertIsNotNone(task.completed_at)
    
    def test_mark_for_retry(self):
        """Test đánh dấu task để retry"""
        task = Task.objects.create(**self.task_data)
        
        task.mark_for_retry()
        
        self.assertEqual(task.status, TaskStatus.RETRY)
        self.assertEqual(task.retry_count, 1)
        self.assertIsNotNone(task.next_retry_at)
        self.assertTrue(task.next_retry_at > timezone.now())
    
    def test_can_retry_true(self):
        """Test kiểm tra có thể retry khi chưa hết số lần retry"""
        task = Task.objects.create(**self.task_data)
        task.retry_count = 1
        task.next_retry_at = timezone.now() - timedelta(seconds=1)  # Past time
        task.save()
        
        self.assertTrue(task.can_retry())
    
    def test_can_retry_false_max_retries(self):
        """Test kiểm tra không thể retry khi đã hết số lần retry"""
        task = Task.objects.create(**self.task_data)
        task.retry_count = 3  # Equal to max_retries
        task.next_retry_at = timezone.now() - timedelta(seconds=1)
        task.save()
        
        self.assertFalse(task.can_retry())
    
    def test_can_retry_false_future_time(self):
        """Test kiểm tra không thể retry khi chưa đến thời gian retry"""
        task = Task.objects.create(**self.task_data)
        task.retry_count = 1
        task.next_retry_at = timezone.now() + timedelta(seconds=60)  # Future time
        task.save()
        
        self.assertFalse(task.can_retry())


class TestTaskLogModel(TestCase):
    """Test cases cho TaskLog model"""
    
    def setUp(self):
        """Setup trước mỗi test"""
        self.task = Task.objects.create(
            task_name='test_task',
            queue_name='test_queue'
        )
    
    def test_create_task_log(self):
        """Test tạo task log"""
        log = TaskLog.objects.create(
            task=self.task,
            level='INFO',
            message='Test log message'
        )
        
        self.assertEqual(log.task, self.task)
        self.assertEqual(log.level, 'INFO')
        self.assertEqual(log.message, 'Test log message')
        self.assertIsNotNone(log.timestamp)
    
    def test_task_log_str(self):
        """Test string representation của TaskLog"""
        log = TaskLog.objects.create(
            task=self.task,
            level='ERROR',
            message='This is a very long error message that should be truncated'
        )
        
        expected_str = f"{self.task.id} - ERROR: This is a very long error message that should be t"
        self.assertEqual(str(log), expected_str) 