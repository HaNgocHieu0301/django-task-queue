import logging
import importlib
from typing import Dict, Callable, Any
from django.conf import settings

logger = logging.getLogger(__name__)


class TaskRegistry:
    """
    Registry để đăng ký và quản lý các task functions
    """
    
    def __init__(self):
        self._tasks: Dict[str, Callable] = {}
        self._loaded = False
    
    def register(self, name: str = None):
        """
        Decorator để đăng ký task function
        
        Usage:
            @task_registry.register('my_task')
            def my_task_function(arg1, arg2):
                return arg1 + arg2
        """
        def decorator(func: Callable):
            task_name = name or func.__name__
            self._tasks[task_name] = func
            logger.info(f"Registered task: {task_name}")
            return func
        return decorator
    
    def get_task(self, name: str) -> Callable:
        """
        Lấy task function theo tên
        
        Args:
            name: Tên của task
            
        Returns:
            Task function
            
        Raises:
            KeyError: Nếu task không tồn tại
        """
        if not self._loaded:
            self.autodiscover()
        
        if name not in self._tasks:
            raise KeyError(f"Task '{name}' not found. Available tasks: {list(self._tasks.keys())}")
        
        return self._tasks[name]
    
    def list_tasks(self) -> Dict[str, str]:
        """
        Lấy danh sách tất cả tasks đã đăng ký
        
        Returns:
            Dictionary với key là tên task, value là docstring
        """
        if not self._loaded:
            self.autodiscover()
        
        return {
            name: func.__doc__ or "No description"
            for name, func in self._tasks.items()
        }
    
    def autodiscover(self):
        """
        Tự động tìm và import các task modules
        """
        if self._loaded:
            return
        
        # Import tasks từ settings
        task_modules = getattr(settings, 'TASK_MODULES', [])
        
        for module_path in task_modules:
            try:
                importlib.import_module(module_path)
                logger.info(f"Loaded task module: {module_path}")
            except ImportError as e:
                logger.error(f"Failed to import task module {module_path}: {e}")
        
        # Import tasks từ các Django apps
        from django.apps import apps
        for app_config in apps.get_app_configs():
            try:
                module_path = f"{app_config.name}.tasks"
                importlib.import_module(module_path)
                logger.info(f"Loaded tasks from app: {app_config.name}")
            except ImportError:
                # App không có tasks module, bỏ qua
                pass
        
        self._loaded = True
        logger.info(f"Task autodiscovery completed. Found {len(self._tasks)} tasks.")


# Global task registry instance
task_registry = TaskRegistry() 