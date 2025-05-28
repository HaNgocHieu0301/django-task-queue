import time
import threading
from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings
from rest_framework.test import APITestCase
from rest_framework import status
from tasks.models import Task, TaskStatus, TaskPriority
from django_task_queue.queue_manager import QueueManager
from django_task_queue.worker import Worker
from django_task_queue.task_registry import TaskRegistry


class TaskQueueIntegrationTest(TransactionTestCase):
    """
    Integration test for entire task queue system
    """
    
    def setUp(self):
        """Setup test environment"""
        self.queue_manager = QueueManager("test_queue")
        
        # Register test tasks
        self.test_registry = TaskRegistry()
        
        @self.test_registry.register('test_add')
        def test_add(a, b):
            return a + b
        
        @self.test_registry.register('test_multiply')
        def test_multiply(a, b):
            return a * b
        
        @self.test_registry.register('test_failing')
        def test_failing():
            raise Exception("Test failure")
    
    def test_end_to_end_task_processing(self):
        """Test end-to-end: enqueue -> worker process -> complete"""
        # 1. Enqueue task
        task_id = self.queue_manager.enqueue_task(
            task_name="test_add",
            args=[5, 3],
            priority=TaskPriority.HIGH,
            queue_name="test_queue"
        )
        
        # Verify task created in database
        task = Task.objects.get(id=task_id)
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.args, [5, 3])
        
        # 2. Process task with worker
        worker = Worker(
            queue_name="test_queue",
            worker_id="test_worker",
            max_tasks_per_run=1
        )
        
        # Mock task registry to use our test registry
        with self.patch_task_registry():
            # Process one task
            result = worker._process_next_task()
            self.assertTrue(result)
        
        # 3. Verify task completed
        task.refresh_from_db()
        self.assertEqual(task.status, TaskStatus.SUCCESS)
        self.assertEqual(task.result, 8)  # 5 + 3
        self.assertIsNotNone(task.completed_at)
        self.assertEqual(worker.tasks_processed, 1)
    
    def test_task_failure_and_retry(self):
        """Test task failure and retry mechanism"""
        # Enqueue failing task
        task_id = self.queue_manager.enqueue_task(
            task_name="test_failing",
            max_retries=2,
            retry_delay=1,
            queue_name="test_queue"
        )
        
        worker = Worker(
            queue_name="test_queue",
            max_tasks_per_run=1
        )
        
        with self.patch_task_registry():
            # First attempt - should fail and retry
            result = worker._process_next_task()
            self.assertTrue(result)
        
        # Check task is marked for retry
        task = Task.objects.get(id=task_id)
        self.assertEqual(task.status, TaskStatus.RETRY)
        self.assertEqual(task.retry_count, 1)
        self.assertIsNotNone(task.next_retry_at)
        
        # Manually process retry queue
        from django.utils import timezone
        task.next_retry_at = timezone.now() - timezone.timedelta(seconds=10)
        task.save()
        
        # Process retry queue
        self.queue_manager.process_retry_queue()
        
        # Check task is back in pending
        task.refresh_from_db()
        self.assertEqual(task.status, TaskStatus.PENDING)
    
    def test_multiple_workers_concurrent_processing(self):
        """Test multiple workers processing tasks concurrently"""
        # Enqueue multiple tasks
        task_ids = []
        for i in range(5):
            task_id = self.queue_manager.enqueue_task(
                task_name="test_multiply",
                args=[i, 2],
                queue_name="test_queue"
            )
            task_ids.append(task_id)
        
        # Create multiple workers
        workers = []
        threads = []
        
        for i in range(3):
            worker = Worker(
                queue_name="test_queue",
                worker_id=f"worker_{i}",
                max_tasks_per_run=2,
                poll_interval=0.1
            )
            workers.append(worker)
        
        # Start workers in threads
        with self.patch_task_registry():
            for worker in workers:
                thread = threading.Thread(target=worker.start)
                thread.daemon = True
                thread.start()
                threads.append(thread)
            
            # Wait for workers to process tasks
            time.sleep(2)
            
            # Stop workers
            for worker in workers:
                worker.stop()
        
        # Verify all tasks completed
        completed_tasks = Task.objects.filter(
            id__in=task_ids,
            status=TaskStatus.SUCCESS
        ).count()
        
        self.assertEqual(completed_tasks, 5)
        
        # Verify results
        for i, task_id in enumerate(task_ids):
            task = Task.objects.get(id=task_id)
            self.assertEqual(task.result, i * 2)
    
    def test_queue_stats(self):
        """Test queue statistics"""
        # Clear any existing tasks first
        from django_task_queue.redis_client import redis_client
        redis = redis_client.get_connection()
        redis.flushdb()
        
        # Enqueue some tasks
        for i in range(3):
            self.queue_manager.enqueue_task(
                task_name="test_add",
                args=[i, 1],
                queue_name="test_queue"
            )
        
        stats = self.queue_manager.get_queue_stats()
        
        self.assertEqual(stats["pending"], 3)
        self.assertEqual(stats["processing"], 0)
        self.assertEqual(stats["completed"], 0)
    
    def patch_task_registry(self):
        """Context manager to patch task registry with test registry"""
        from unittest.mock import patch
        return patch('django_task_queue.worker.task_registry', self.test_registry)


class TaskAPIIntegrationTest(APITestCase):
    """
    Integration test for Task API
    """
    
    def test_create_and_process_task_via_api(self):
        """Test creating task via API and processing with worker"""
        # 1. Create task via API
        url = '/api/tasks/'
        data = {
            'task_name': 'add_numbers',
            'args': [10, 20],
            'priority': 'high',
            'max_retries': 2
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        task_data = response.data['data']
        task_id = task_data['id']
        
        # 2. Verify task in database
        task = Task.objects.get(id=task_id)
        self.assertEqual(task.task_name, 'add_numbers')
        self.assertEqual(task.args, [10, 20])
        self.assertEqual(task.priority, 3)  # TaskPriority.HIGH = 3
        self.assertEqual(task.status, TaskStatus.PENDING)
        
        # 3. List tasks via API
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['count'], 1)
        
        # 4. Filter tasks by status
        response = self.client.get(url + '?status=pending')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        
        response = self.client.get(url + '?status=success')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
    
    def test_api_validation_errors(self):
        """Test API validation errors"""
        url = '/api/tasks/'
        
        # Missing task_name
        data = {'args': [1, 2]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        
        # Invalid priority
        data = {
            'task_name': 'test_task',
            'priority': 'invalid_priority'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Invalid args type
        data = {
            'task_name': 'test_task',
            'args': 'not_a_list'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Invalid kwargs type
        data = {
            'task_name': 'test_task',
            'kwargs': 'not_a_dict'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TaskRetryIntegrationTest(TransactionTestCase):
    """
    Integration test for retry mechanism - simplified
    """
    
    def test_task_retry_mechanism(self):
        """Test basic retry mechanism"""
        queue_manager = QueueManager("retry_test_queue")
        
        # Enqueue failing task
        task_id = queue_manager.enqueue_task(
            task_name="failing_task",
            kwargs={'should_fail': True},
            max_retries=2,
            retry_delay=1,
            queue_name="retry_test_queue"
        )
        
        # Verify task created
        task = Task.objects.get(id=task_id)
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.retry_count, 0)
        
        # Test that task can be marked for retry
        task.mark_for_retry()
        self.assertEqual(task.status, TaskStatus.RETRY)
        self.assertEqual(task.retry_count, 1)
        self.assertIsNotNone(task.next_retry_at)
        
        # Test retry queue processing
        from django.utils import timezone
        task.next_retry_at = timezone.now() - timezone.timedelta(seconds=10)
        task.save()
        
        queue_manager.process_retry_queue()
        
        task.refresh_from_db()
        self.assertEqual(task.status, TaskStatus.PENDING) 