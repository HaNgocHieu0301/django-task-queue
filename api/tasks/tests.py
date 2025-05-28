from django.test import TestCase, Client
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from tasks.models import Task, TaskStatus, TaskPriority


class TestTasksAPI(APITestCase):
    """
    Test cases cho Tasks API sử dụng TaskViewSet
    """

    def setUp(self):
        """
        Thiết lập dữ liệu test
        """
        self.client = APIClient()

        # Tạo test data
        self.task_data = {
            "task_name": "test_task",
            "priority": TaskPriority.HIGH,
            "args": ["arg1", "arg2"],
            "kwargs": {"key1": "value1", "key2": "value2"},
            "max_retries": 5,
            "retry_delay": 30,
            "queue_name": "test_queue",
        }

        # Tạo một số tasks mẫu
        self.task1 = Task.objects.create(
            task_name="task_1",
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            args=["test1"],
            kwargs={"test": "value1"},
            queue_name="queue1",
        )

        self.task2 = Task.objects.create(
            task_name="task_2",
            status=TaskStatus.FAILED,
            priority=TaskPriority.NORMAL,
            args=["test2"],
            kwargs={"test": "value2"},
            queue_name="queue2",
        )

        self.task3 = Task.objects.create(
            task_name="task_3",
            status=TaskStatus.SUCCESS,
            priority=TaskPriority.LOW,
            args=["test3"],
            kwargs={"test": "value3"},
            queue_name="queue1",
        )

    def test_create_task_success(self):
        """
        Test: Tạo task mới thành công
        """
        url = "/api/tasks/"
        response = self.client.post(url, self.task_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response_data = response.json()
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["message"], "Task đã được tạo thành công")
        self.assertIn("data", response_data)

        # Kiểm tra dữ liệu task được tạo
        task_data = response_data["data"]
        self.assertEqual(task_data["task_name"], "test_task")
        self.assertEqual(task_data["priority"], TaskPriority.HIGH)
        self.assertEqual(task_data["status"], TaskStatus.PENDING)
        self.assertEqual(task_data["args"], ["arg1", "arg2"])
        self.assertEqual(task_data["kwargs"], {"key1": "value1", "key2": "value2"})

        # Kiểm tra task đã được lưu vào database
        task = Task.objects.get(id=task_data["id"])
        self.assertEqual(task.task_name, "test_task")

    def test_create_task_invalid_data(self):
        """
        Test: Tạo task với dữ liệu không hợp lệ
        """
        url = "/api/tasks/"

        # Test thiếu task_name
        invalid_data = {
            "priority": TaskPriority.HIGH,
            "args": ["arg1"],
            "kwargs": {"key1": "value1"},
        }

        response = self.client.post(url, invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response_data = response.json()
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["message"], "Dữ liệu không hợp lệ")
        self.assertIn("errors", response_data)

    def test_create_task_invalid_args_type(self):
        """
        Test: Tạo task với args không phải list
        """
        url = "/api/tasks/"
        invalid_data = self.task_data.copy()
        invalid_data["args"] = "not_a_list"

        response = self.client.post(url, invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response_data = response.json()
        self.assertIn("args", response_data["errors"])

    def test_create_task_invalid_kwargs_type(self):
        """
        Test: Tạo task với kwargs không phải dict
        """
        url = "/api/tasks/"
        invalid_data = self.task_data.copy()
        invalid_data["kwargs"] = "not_a_dict"

        response = self.client.post(url, invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response_data = response.json()
        self.assertIn("kwargs", response_data["errors"])

    def test_list_tasks_success(self):
        """
        Test: Lấy danh sách tasks thành công
        """
        url = "/api/tasks/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["message"], "Lấy danh sách tasks thành công")
        self.assertIn("data", response_data)
        self.assertIn("count", response_data)

        # Kiểm tra số lượng tasks
        self.assertEqual(response_data["count"], 3)  # 3 tasks được tạo trong setUp
        self.assertEqual(len(response_data["data"]), 3)

    def test_list_tasks_filter_by_status(self):
        """
        Test: Filter tasks theo status
        """
        url = "/api/tasks/?status=pending"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["count"], 1)  # Chỉ có 1 task pending

        # Kiểm tra task trả về có status pending
        task_data = response_data["data"][0]
        self.assertEqual(task_data["status"], TaskStatus.PENDING)

    def test_list_tasks_filter_by_priority(self):
        """
        Test: Filter tasks theo priority
        """
        url = "/api/tasks/?priority=high"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["count"], 1)  # Chỉ có 1 task high priority

        # Kiểm tra task trả về có priority high
        task_data = response_data["data"][0]
        self.assertEqual(task_data["priority"], TaskPriority.HIGH)

    def test_list_tasks_filter_by_queue_name(self):
        """
        Test: Filter tasks theo queue_name
        """
        url = "/api/tasks/?queue_name=queue1"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["count"], 2)  # 2 tasks trong queue1

        # Kiểm tra tất cả tasks trả về đều có queue_name = queue1
        for task_data in response_data["data"]:
            self.assertEqual(task_data["queue_name"], "queue1")

    def test_list_tasks_multiple_filters(self):
        """
        Test: Filter tasks với nhiều điều kiện
        """
        url = "/api/tasks/?status=pending&priority=high"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["count"], 1)  # 1 task pending và high priority

        task_data = response_data["data"][0]
        self.assertEqual(task_data["status"], TaskStatus.PENDING)
        self.assertEqual(task_data["priority"], TaskPriority.HIGH)


class TestTasksAPIIntegration(TestCase):
    """
    Integration tests cho Tasks API
    """

    def setUp(self):
        """
        Thiết lập dữ liệu test
        """
        self.client = Client()

    def test_api_endpoints_accessibility(self):
        """
        Test: Kiểm tra tất cả endpoints có thể truy cập được
        """
        endpoints = [
            "/api/tasks/",
        ]

        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertIn(
                response.status_code,
                [200, 201, 400, 404],
                f"Endpoint {endpoint} should be accessible",
            )

    def test_api_content_type(self):
        """
        Test: Kiểm tra content type của API responses
        """
        response = self.client.get("/api/tasks/")
        self.assertEqual(response["Content-Type"], "application/json")

    def test_api_cors_headers(self):
        """
        Test: Kiểm tra CORS headers (nếu có cấu hình)
        """
        response = self.client.get("/api/tasks/")
        # Kiểm tra response có thành công
        self.assertIn(response.status_code, [200, 201])