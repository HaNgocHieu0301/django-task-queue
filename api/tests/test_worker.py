import time
import threading
from unittest.mock import patch, MagicMock, call
from django.test import TestCase
from django_task_queue.worker import Worker, WorkerPool
from django_task_queue.task_registry import TaskRegistry
from tasks.models import Task, TaskStatus, TaskPriority


class TestWorker(TestCase):
    """
    Test cases for Worker
    """
    
    def setUp(self):
        """Setup test environment"""
        self.worker = Worker(
            queue_name="test_queue",
            worker_id="test_worker",
            poll_interval=0.1,  # Faster polling for tests
            max_tasks_per_run=1  # Process only 1 task then stop
        )
    
    @patch('django_task_queue.worker.QueueManager')
    def test_worker_initialization(self, mock_queue_manager):
        """Test worker initialization"""
        worker = Worker(
            queue_name="custom_queue",
            worker_id="custom_worker",
            poll_interval=2,
            max_tasks_per_run=5
        )
        
        self.assertEqual(worker.queue_name, "custom_queue")
        self.assertEqual(worker.worker_id, "custom_worker")
        self.assertEqual(worker.poll_interval, 2)
        self.assertEqual(worker.max_tasks_per_run, 5)
        self.assertFalse(worker.running)
        self.assertEqual(worker.tasks_processed, 0)
    
    def test_worker_auto_id_generation(self):
        """Test worker automatically generates ID if not provided"""
        worker = Worker()
        
        self.assertTrue(worker.worker_id.startswith("worker_"))
        self.assertEqual(len(worker.worker_id), 15)  # "worker_" + 8 chars
    
    @patch('django_task_queue.worker.QueueManager')
    def test_stop_worker(self, mock_queue_manager):
        """Test stopping worker"""
        worker = Worker()
        worker.running = True
        worker.tasks_processed = 5
        
        worker.stop()
        
        self.assertFalse(worker.running)
    
    @patch('django_task_queue.worker.task_registry')
    @patch('django_task_queue.worker.QueueManager')
    def test_process_task_success(self, mock_queue_manager_class, mock_task_registry):
        """Test successful task processing"""
        # Setup mocks
        mock_queue_manager = MagicMock()
        mock_queue_manager_class.return_value = mock_queue_manager
        
        # Mock task data
        task_data = {
            "task_id": "test-task-id",
            "task_name": "test_task",
            "args": [1, 2],
            "kwargs": {"key": "value"}
        }
        mock_queue_manager.dequeue_task.return_value = task_data
        
        # Mock task function
        mock_task_func = MagicMock(return_value="task result")
        mock_task_registry.get_task.return_value = mock_task_func
        
        worker = Worker()
        result = worker._process_next_task()
        
        # Check result
        self.assertTrue(result)
        self.assertEqual(worker.tasks_processed, 1)
        
        # Check methods are called
        mock_queue_manager.dequeue_task.assert_called_once()
        mock_task_registry.get_task.assert_called_once_with("test_task")
        mock_task_func.assert_called_once_with(1, 2, key="value")
        mock_queue_manager.complete_task.assert_called_once_with(
            "test-task-id", worker.worker_id, "task result"
        )
    
    @patch('django_task_queue.worker.task_registry')
    @patch('django_task_queue.worker.QueueManager')
    def test_process_task_not_found(self, mock_queue_manager_class, mock_task_registry):
        """Test processing task when function not found"""
        # Setup mocks
        mock_queue_manager = MagicMock()
        mock_queue_manager_class.return_value = mock_queue_manager
        
        task_data = {
            "task_id": "test-task-id",
            "task_name": "unknown_task",
            "args": [],
            "kwargs": {}
        }
        mock_queue_manager.dequeue_task.return_value = task_data
        
        # Mock task registry raise KeyError
        mock_task_registry.get_task.side_effect = KeyError("Task not found")
        
        worker = Worker()
        result = worker._process_next_task()
        
        # Check result
        self.assertTrue(result)  # Still return True because error was handled
        self.assertEqual(worker.tasks_processed, 0)  # Don't increment counter
        
        # Check fail_task is called
        mock_queue_manager.fail_task.assert_called_once()
        args = mock_queue_manager.fail_task.call_args[0]
        self.assertEqual(args[0], "test-task-id")
        self.assertEqual(args[1], worker.worker_id)
        self.assertIn("Task function not found", args[2])
    
    @patch('django_task_queue.worker.task_registry')
    @patch('django_task_queue.worker.QueueManager')
    def test_process_task_execution_error(self, mock_queue_manager_class, mock_task_registry):
        """Test processing task with execution error"""
        # Setup mocks
        mock_queue_manager = MagicMock()
        mock_queue_manager_class.return_value = mock_queue_manager
        
        task_data = {
            "task_id": "test-task-id",
            "task_name": "failing_task",
            "args": [],
            "kwargs": {}
        }
        mock_queue_manager.dequeue_task.return_value = task_data
        
        # Mock task function raise exception
        mock_task_func = MagicMock(side_effect=Exception("Task execution failed"))
        mock_task_registry.get_task.return_value = mock_task_func
        
        worker = Worker()
        result = worker._process_next_task()
        
        # Check result
        self.assertTrue(result)
        self.assertEqual(worker.tasks_processed, 0)
        
        # Check fail_task is called
        mock_queue_manager.fail_task.assert_called_once()
        args = mock_queue_manager.fail_task.call_args[0]
        self.assertEqual(args[0], "test-task-id")
        self.assertIn("Task execution failed", args[2])
    
    @patch('django_task_queue.worker.QueueManager')
    def test_process_no_task_available(self, mock_queue_manager_class):
        """Test processing when no task available"""
        mock_queue_manager = MagicMock()
        mock_queue_manager_class.return_value = mock_queue_manager
        mock_queue_manager.dequeue_task.return_value = None
        
        worker = Worker()
        result = worker._process_next_task()
        
        self.assertFalse(result)
        self.assertEqual(worker.tasks_processed, 0)
    
    @patch('django_task_queue.worker.QueueManager')
    def test_get_stats(self, mock_queue_manager_class):
        """Test getting worker statistics"""
        mock_queue_manager = MagicMock()
        mock_queue_manager_class.return_value = mock_queue_manager
        mock_queue_manager.get_queue_stats.return_value = {
            "pending": 5,
            "processing": 2,
            "completed": 10
        }
        
        worker = Worker(queue_name="test_queue", worker_id="test_worker")
        worker.running = True
        worker.tasks_processed = 3
        
        with patch('django_task_queue.worker.task_registry') as mock_registry:
            mock_registry.list_tasks.return_value = {"task1": "desc1", "task2": "desc2"}
            
            stats = worker.get_stats()
        
        expected_stats = {
            "worker_id": "test_worker",
            "queue_name": "test_queue",
            "running": True,
            "tasks_processed": 3,
            "queue_stats": {
                "pending": 5,
                "processing": 2,
                "completed": 10
            },
            "available_tasks": ["task1", "task2"]
        }
        
        self.assertEqual(stats, expected_stats)


class TestWorkerPool(TestCase):
    """
    Test cases for WorkerPool
    """
    
    def test_worker_pool_initialization(self):
        """Test worker pool initialization"""
        pool = WorkerPool(num_workers=3, queue_name="test_queue")
        
        self.assertEqual(pool.num_workers, 3)
        self.assertEqual(pool.queue_name, "test_queue")
        self.assertEqual(len(pool.workers), 0)
        self.assertEqual(len(pool.threads), 0)
    
    @patch('django_task_queue.worker.Worker')
    @patch('threading.Thread')
    def test_worker_pool_start(self, mock_thread_class, mock_worker_class):
        """Test starting worker pool"""
        # Setup mocks
        mock_workers = [MagicMock() for _ in range(2)]
        mock_worker_class.side_effect = mock_workers
        
        mock_threads = [MagicMock() for _ in range(2)]
        mock_thread_class.side_effect = mock_threads
        
        pool = WorkerPool(num_workers=2, queue_name="test_queue")
        
        # Mock thread.join() to not block test
        for thread in mock_threads:
            thread.join.return_value = None
        
        pool.start()
        
        # Check workers are created
        self.assertEqual(len(pool.workers), 2)
        self.assertEqual(mock_worker_class.call_count, 2)
        
        # Check worker IDs
        worker_calls = mock_worker_class.call_args_list
        self.assertEqual(worker_calls[0][1]['queue_name'], "test_queue")
        self.assertEqual(worker_calls[0][1]['worker_id'], "worker_test_queue_1")
        self.assertEqual(worker_calls[1][1]['worker_id'], "worker_test_queue_2")
        
        # Check threads are created and started
        self.assertEqual(mock_thread_class.call_count, 2)
        for thread in mock_threads:
            thread.start.assert_called_once()
            thread.join.assert_called_once()
    
    def test_worker_pool_stop(self):
        """Test stopping worker pool"""
        pool = WorkerPool(num_workers=2)
        
        # Add mock workers
        mock_worker1 = MagicMock()
        mock_worker2 = MagicMock()
        pool.workers = [mock_worker1, mock_worker2]
        
        pool.stop()
        
        # Check stop is called for all workers
        mock_worker1.stop.assert_called_once()
        mock_worker2.stop.assert_called_once()
    
    def test_worker_pool_get_stats(self):
        """Test getting worker pool statistics"""
        pool = WorkerPool(num_workers=2, queue_name="test_queue")
        
        # Add mock workers with stats
        mock_worker1 = MagicMock()
        mock_worker1.get_stats.return_value = {"worker_id": "worker1", "tasks_processed": 5}
        
        mock_worker2 = MagicMock()
        mock_worker2.get_stats.return_value = {"worker_id": "worker2", "tasks_processed": 3}
        
        pool.workers = [mock_worker1, mock_worker2]
        
        stats = pool.get_stats()
        
        expected_stats = {
            "pool_size": 2,
            "queue_name": "test_queue",
            "workers": [
                {"worker_id": "worker1", "tasks_processed": 5},
                {"worker_id": "worker2", "tasks_processed": 3}
            ]
        }
        
        self.assertEqual(stats, expected_stats) 