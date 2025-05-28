from django.db import models
import uuid


class TaskStatus(models.TextChoices):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"
    CANCELLED = "cancelled"


class TaskPriority(models.TextChoices):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Task(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task_name = models.CharField(max_length=255, help_text="Tên của task function")
    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.PENDING,
    )
    priority = models.CharField(
        max_length=10,
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
