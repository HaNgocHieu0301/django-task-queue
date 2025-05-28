import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

from tasks.models import Task, TaskStatus, TaskPriority


class TestTaskViewSet(TestCase):
    """Test cases cho TaskViewSet"""
    
    def setUp(self):
        """Setup trước mỗi test"""
        self.client = APIClient()
        self.create_url = '/api/tasks/'
        self.list_url = '/api/tasks/'
        
        # Clear existing tasks
        Task.objects.all().delete()
    
    def tearDown(self):
        """Cleanup sau mỗi test"""
        Task.objects.all().delete()
    
    @patch('tasks.views.queue_manager.enqueue_task')
    def test_create_task_success(self, mock_enqueue):
        """Test tạo task thành công"""
        # Mock queue_manager.enqueue_task return value
        mock_task_id = "12345678-1234-1234-1234-123456789012"
        mock_enqueue.return_value = mock_task_id
        
        # Create a task in database for the mock
        task = Task.objects.create(
            id=mock_task_id,
            task_name="test_function",
            args=["arg1", "arg2"],
            kwargs={"key": "value"},
            priority=TaskPriority.HIGH,
            max_retries=5,
            retry_delay=120,
            queue_name="default"
        )
        
        data = {
            "task_name": "test_function",
            "priority": "high",
            "args": ["arg1", "arg2"],
            "kwargs": {"key": "value"},
            "max_retries": 5,
            "retry_delay": 120,
            "queue_name": "default"
        }
        
        response = self.client.post(
            self.create_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['message'], 'Task đã được tạo thành công')
        self.assertIn('data', response_data)
        
        # Verify queue_manager.enqueue_task was called with correct parameters
        mock_enqueue.assert_called_once_with(
            task_name="test_function",
            priority=TaskPriority.HIGH,
            args=["arg1", "arg2"],
            kwargs={"key": "value"},
            max_retries=5,
            retry_delay=120,
            queue_name="default"
        )
    
    @patch('tasks.views.queue_manager.enqueue_task')
    def test_create_task_with_defaults(self, mock_enqueue):
        """Test tạo task với các giá trị mặc định"""
        mock_task_id = "12345678-1234-1234-1234-123456789012"
        mock_enqueue.return_value = mock_task_id
        
        # Create a task in database for the mock
        task = Task.objects.create(
            id=mock_task_id,
            task_name="simple_task",
            queue_name="default"
        )
        
        data = {
            "task_name": "simple_task"
        }
        
        response = self.client.post(
            self.create_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify default values were used
        mock_enqueue.assert_called_once_with(
            task_name="simple_task",
            priority=TaskPriority.NORMAL,
            args=[],
            kwargs={},
            max_retries=3,
            retry_delay=60,
            queue_name="default"
        )
    
    def test_create_task_invalid_data(self):
        """Test tạo task với dữ liệu không hợp lệ"""
        data = {
            # Missing required task_name
            "priority": "high"
        }
        
        response = self.client.post(
            self.create_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['message'], 'Dữ liệu không hợp lệ')
        self.assertIn('errors', response_data)
    
    def test_create_task_invalid_priority(self):
        """Test tạo task với priority không hợp lệ"""
        data = {
            "task_name": "test_function",
            "priority": "invalid_priority"
        }
        
        response = self.client.post(
            self.create_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertIn('errors', response_data)
    
    def test_list_tasks_empty(self):
        """Test lấy danh sách tasks khi rỗng"""
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['message'], 'Lấy danh sách tasks thành công')
        self.assertEqual(response_data['data'], [])
        self.assertEqual(response_data['count'], 0)
    
    def test_list_tasks_with_data(self):
        """Test lấy danh sách tasks có dữ liệu"""
        # Tạo một số tasks
        task1 = Task.objects.create(
            task_name="task1",
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            queue_name="queue1"
        )
        task2 = Task.objects.create(
            task_name="task2",
            status=TaskStatus.SUCCESS,
            priority=TaskPriority.LOW,
            queue_name="queue2"
        )
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertEqual(len(response_data['data']), 2)
        self.assertEqual(response_data['count'], 2)
        
        # Verify task data
        task_names = [task['task_name'] for task in response_data['data']]
        self.assertIn('task1', task_names)
        self.assertIn('task2', task_names)
    
    def test_list_tasks_filter_by_status(self):
        """Test lấy danh sách tasks với filter theo status"""
        # Tạo tasks với status khác nhau
        Task.objects.create(
            task_name="pending_task",
            status=TaskStatus.PENDING,
            queue_name="test"
        )
        Task.objects.create(
            task_name="success_task",
            status=TaskStatus.SUCCESS,
            queue_name="test"
        )
        Task.objects.create(
            task_name="failed_task",
            status=TaskStatus.FAILED,
            queue_name="test"
        )
        
        # Filter by pending status
        response = self.client.get(f"{self.list_url}?status=pending")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertEqual(len(response_data['data']), 1)
        self.assertEqual(response_data['data'][0]['task_name'], 'pending_task')
        self.assertEqual(response_data['data'][0]['status'], 'pending')
    
    def test_list_tasks_filter_by_priority(self):
        """Test lấy danh sách tasks với filter theo priority"""
        # Tạo tasks với priority khác nhau
        Task.objects.create(
            task_name="high_priority_task",
            priority=TaskPriority.HIGH,
            queue_name="test"
        )
        Task.objects.create(
            task_name="low_priority_task",
            priority=TaskPriority.LOW,
            queue_name="test"
        )
        
        # Filter by high priority
        response = self.client.get(f"{self.list_url}?priority={TaskPriority.HIGH}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertEqual(len(response_data['data']), 1)
        self.assertEqual(response_data['data'][0]['task_name'], 'high_priority_task')
        self.assertEqual(response_data['data'][0]['priority'], TaskPriority.HIGH)
    
    def test_list_tasks_filter_by_queue_name(self):
        """Test lấy danh sách tasks với filter theo queue_name"""
        # Tạo tasks với queue_name khác nhau
        Task.objects.create(
            task_name="queue1_task",
            queue_name="queue1"
        )
        Task.objects.create(
            task_name="queue2_task",
            queue_name="queue2"
        )
        
        # Filter by queue1
        response = self.client.get(f"{self.list_url}?queue_name=queue1")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertEqual(len(response_data['data']), 1)
        self.assertEqual(response_data['data'][0]['task_name'], 'queue1_task')
        self.assertEqual(response_data['data'][0]['queue_name'], 'queue1')
    
    def test_list_tasks_multiple_filters(self):
        """Test lấy danh sách tasks với nhiều filters"""
        # Tạo tasks với các thuộc tính khác nhau
        Task.objects.create(
            task_name="target_task",
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            queue_name="target_queue"
        )
        Task.objects.create(
            task_name="other_task",
            status=TaskStatus.SUCCESS,
            priority=TaskPriority.HIGH,
            queue_name="target_queue"
        )
        Task.objects.create(
            task_name="another_task",
            status=TaskStatus.PENDING,
            priority=TaskPriority.LOW,
            queue_name="target_queue"
        )
        
        # Filter by multiple criteria
        response = self.client.get(
            f"{self.list_url}?status=pending&priority={TaskPriority.HIGH}&queue_name=target_queue"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertEqual(len(response_data['data']), 1)
        self.assertEqual(response_data['data'][0]['task_name'], 'target_task')
    
    @patch('tasks.views.queue_manager.enqueue_task')
    def test_create_task_queue_manager_error(self, mock_enqueue):
        """Test xử lý lỗi từ queue_manager khi tạo task"""
        mock_enqueue.side_effect = Exception("Queue manager error")
        
        data = {
            "task_name": "test_function"
        }
        
        response = self.client.post(
            self.create_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Should return 500 or handle error gracefully
        # This depends on how error handling is implemented in the view
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR])
    
    def test_list_tasks_ordering(self):
        """Test ordering của danh sách tasks"""
        # Tạo tasks với thời gian khác nhau
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        
        task1 = Task.objects.create(
            task_name="old_task",
            queue_name="test"
        )
        task1.created_at = now - timedelta(hours=2)
        task1.save()
        
        task2 = Task.objects.create(
            task_name="new_task",
            queue_name="test"
        )
        task2.created_at = now - timedelta(hours=1)
        task2.save()
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertEqual(len(response_data['data']), 2)
        
        # Should be ordered by created_at descending (newest first)
        self.assertEqual(response_data['data'][0]['task_name'], 'new_task')
        self.assertEqual(response_data['data'][1]['task_name'], 'old_task') 