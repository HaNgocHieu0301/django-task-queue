from django.db import models
import uuid
from django.utils import timezone
from datetime import timedelta
from typing import Any

class TaskStatus(models.TextChoices):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"
    CANCELLED = "cancelled"


class TaskPriority(models.TextChoices):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4 


class Task(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task_name = models.CharField(max_length=255, help_text="Tên của task function")
    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.PENDING,
    )
    priority = models.IntegerField(
        choices=TaskPriority.choices,
        default=TaskPriority.NORMAL,
    )

    # Task data
    args = models.JSONField(default=list, help_text="Arguments cho task")
    kwargs = models.JSONField(default=dict, help_text="Keyword arguments cho task")
    result = models.JSONField(null=True, blank=True, help_text="Kết quả của task")
    error_message = models.TextField(
        null=True, blank=True, help_text="Thông báo lỗi nếu task thất bại"
    )

    # Retry logic
    retry_count = models.PositiveIntegerField(default=0, help_text="Số lần đã retry")
    max_retries = models.PositiveIntegerField(
        default=3, help_text="Số lần retry tối đa"
    )
    retry_delay = models.PositiveIntegerField(
        default=60, help_text="Thời gian delay giữa các lần retry (seconds)"
    )
    next_retry_at = models.DateTimeField(
        null=True, blank=True, help_text="Thời gian retry tiếp theo"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(
        null=True, blank=True, help_text="Thời gian bắt đầu xử lý"
    )
    completed_at = models.DateTimeField(
        null=True, blank=True, help_text="Thời gian hoàn thành"
    )

    # Metadata
    worker_id = models.CharField(
        max_length=255, null=True, blank=True, help_text="ID của worker xử lý task"
    )
    queue_name = models.CharField(
        max_length=100, default="default", help_text="Tên queue chứa task"
    )

    class Meta:
        db_table = "tasks"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["priority"]),
            models.Index(fields=["queue_name"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["next_retry_at"]),
        ]

    def __str__(self):
        return f"Task {self.task_name} ({self.status})"

    def to_dict(self):
        return {
            'task_id': str(self.id),
            'task_name': self.task_name,
            'args': self.args,
            'kwargs': self.kwargs,
            'priority': self.priority,
            'queue_name': self.queue_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'retry_count': self.retry_count,
            'retry_delay': self.retry_delay,
            'error_message': self.error_message,
        }
    
    def mark_as_processing(self, worker_id: str):
        self.status = TaskStatus.PROCESSING
        self.worker_id = worker_id
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'worker_id', 'started_at'])

    def mark_as_completed(self, result: Any = None):
        self.status = TaskStatus.SUCCESS
        self.completed_at = timezone.now()
        self.result = result
        self.save(update_fields=['status', 'completed_at', 'result'])

    def mark_as_failed(self, error_message: str):
        self.status = TaskStatus.FAILED
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.save(update_fields=['status', 'completed_at', 'error_message'])

    def mark_for_retry(self):
        self.status = TaskStatus.RETRY
        self.retry_count += 1
        self.next_retry_at = timezone.now() + timedelta(seconds=self.retry_delay)
        self.save(update_fields=['status', 'retry_count', 'next_retry_at'])

    def can_retry(self) -> bool:
        # Kiểm tra số lần retry chưa vượt quá max_retries
        if self.retry_count >= self.max_retries:
            return False
        
        # Nếu có next_retry_at, kiểm tra đã đến thời gian retry chưa
        if self.next_retry_at and self.next_retry_at > timezone.now():
            return False
            
        return True


class TaskLog(models.Model):
    """
    Model để lưu trữ log của task
    """

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="logs")
    level = models.CharField(
        max_length=10,
        choices=[
            ("DEBUG", "Debug"),
            ("INFO", "Info"),
            ("WARNING", "Warning"),
            ("ERROR", "Error"),
        ],
    )
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "task_logs"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.task.id} - {self.level}: {self.message[:50]}"
