import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from .task_status import TaskStatus, TaskPriority


class Task:
    """
    Class đại diện cho một task trong queue
    """
    
    def __init__(
        self,
        func_name: str,
        args: tuple = (),
        kwargs: Dict[str, Any] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3,
        retry_delay: int = 60,  # seconds
        timeout: int = 300,     # seconds
        task_id: str = None
    ):
        self.task_id = task_id or str(uuid.uuid4())
        self.func_name = func_name
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.priority = priority
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now(timezone.utc)
        self.started_at = None
        self.completed_at = None
        self.retry_count = 0
        self.error_message = None
        self.result = None