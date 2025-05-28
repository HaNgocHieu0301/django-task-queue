import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.conf import settings
from django_task_queue.task_registry import TaskRegistry, task_registry


class TestTaskRegistry(TestCase):
    """
    Test cases for TaskRegistry
    """
    
    def setUp(self):
        """Setup test environment"""
        self.registry = TaskRegistry()
    
    def test_register_task_with_name(self):
        """Test registering task with specific name"""
        @self.registry.register('custom_task')
        def sample_task():
            return "test result"
        
        # Check task is registered
        self.assertIn('custom_task', self.registry._tasks)
        self.assertEqual(self.registry._tasks['custom_task'], sample_task)
    
    def test_register_task_without_name(self):
        """Test registering task without name (use function name)"""
        @self.registry.register()
        def another_task():
            return "another result"
        
        # Check task is registered with function name
        self.assertIn('another_task', self.registry._tasks)
        self.assertEqual(self.registry._tasks['another_task'], another_task)
    
    def test_get_task_existing(self):
        """Test getting existing task"""
        @self.registry.register('existing_task')
        def existing_task():
            return "existing"
        
        # Force load tasks
        self.registry._loaded = True
        
        retrieved_task = self.registry.get_task('existing_task')
        self.assertEqual(retrieved_task, existing_task)
    
    def test_get_task_not_existing(self):
        """Test getting non-existing task"""
        self.registry._loaded = True
        
        with self.assertRaises(KeyError) as context:
            self.registry.get_task('non_existing_task')
        
        self.assertIn("Task 'non_existing_task' not found", str(context.exception))
    
    def test_list_tasks(self):
        """Test listing all tasks"""
        @self.registry.register('task1')
        def task1():
            """Task 1 description"""
            return "task1"
        
        @self.registry.register('task2')
        def task2():
            """Task 2 description"""
            return "task2"
        
        # Force load tasks
        self.registry._loaded = True
        
        tasks = self.registry.list_tasks()
        
        self.assertIn('task1', tasks)
        self.assertIn('task2', tasks)
        self.assertEqual(tasks['task1'], 'Task 1 description')
        self.assertEqual(tasks['task2'], 'Task 2 description')
    
    def test_list_tasks_no_description(self):
        """Test listing tasks without docstring"""
        @self.registry.register('no_desc_task')
        def no_desc_task():
            return "no desc"
        
        # Force load tasks
        self.registry._loaded = True
        
        tasks = self.registry.list_tasks()
        self.assertEqual(tasks['no_desc_task'], 'No description')
    
    @patch('django.apps.apps.get_app_configs')
    @patch('django_task_queue.task_registry.importlib.import_module')
    def test_autodiscover_task_modules(self, mock_import, mock_get_apps):
        """Test autodiscover from TASK_MODULES settings"""
        # Mock empty app configs
        mock_get_apps.return_value = []
        
        # Mock settings
        with patch.object(settings, 'TASK_MODULES', ['test.module1', 'test.module2']):
            self.registry.autodiscover()
        
        # Check import is called for TASK_MODULES
        self.assertEqual(mock_import.call_count, 2)
        mock_import.assert_any_call('test.module1')
        mock_import.assert_any_call('test.module2')
        
        self.assertTrue(self.registry._loaded)
    
    @patch('django.apps.apps.get_app_configs')
    @patch('django_task_queue.task_registry.importlib.import_module')
    def test_autodiscover_import_error(self, mock_import, mock_get_apps):
        """Test autodiscover when import error occurs"""
        mock_get_apps.return_value = []
        mock_import.side_effect = ImportError("Module not found")
        
        with patch.object(settings, 'TASK_MODULES', ['invalid.module']):
            # Should not raise exception
            self.registry.autodiscover()
        
        self.assertTrue(self.registry._loaded)
    
    @patch('django.apps.apps.get_app_configs')
    @patch('django_task_queue.task_registry.importlib.import_module')
    def test_autodiscover_django_apps(self, mock_import, mock_get_apps):
        """Test autodiscover from Django apps"""
        # Mock app configs
        mock_app1 = MagicMock()
        mock_app1.name = 'app1'
        mock_app2 = MagicMock()
        mock_app2.name = 'app2'
        
        mock_get_apps.return_value = [mock_app1, mock_app2]
        
        # Mock import - app1 has tasks, app2 doesn't
        def import_side_effect(module_path):
            if module_path == 'app2.tasks':
                raise ImportError("No tasks module")
            return MagicMock()
        
        mock_import.side_effect = import_side_effect
        
        with patch.object(settings, 'TASK_MODULES', []):
            self.registry.autodiscover()
        
        # Check import is called for both apps
        mock_import.assert_any_call('app1.tasks')
        mock_import.assert_any_call('app2.tasks')
    
    @patch('django.apps.apps.get_app_configs')
    def test_autodiscover_only_once(self, mock_get_apps):
        """Test autodiscover runs only once"""
        mock_get_apps.return_value = []
        
        with patch('django_task_queue.task_registry.importlib.import_module') as mock_import:
            # Call autodiscover first time
            self.registry.autodiscover()
            first_call_count = mock_import.call_count
            
            # Call second time
            self.registry.autodiscover()
            second_call_count = mock_import.call_count
            
            # Import call count should not change
            self.assertEqual(first_call_count, second_call_count)
    
    def test_global_registry_instance(self):
        """Test global registry instance"""
        from django_task_queue.task_registry import task_registry
        
        # Check it's an instance of TaskRegistry
        self.assertIsInstance(task_registry, TaskRegistry)
        
        # Test register via global instance
        @task_registry.register('global_test')
        def global_test_task():
            return "global test"
        
        self.assertIn('global_test', task_registry._tasks) 