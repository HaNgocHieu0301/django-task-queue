import logging
import json
import redis
import uuid
from typing import Optional, Dict, Any
from django.utils import timezone
from .redis_client import redis_client
from tasks.models import Task, TaskStatus, TaskPriority

logger = logging.getLogger(__name__)


class QueueManager:
    """
    QueueManager quản lý task queue sử dụng Redis làm message broker
    """

    def __init__(self, queue_name: str = "default"):
        self.queue_name = queue_name
        self.redis = redis_client.get_connection()

        # Queue names
        self.PENDING_QUEUE = "task_queue:pending"
        self.PROCESSING_QUEUE = "task_queue:processing"
        self.COMPLETED_QUEUE = "task_queue:completed"
        self.RETRY_QUEUE = "task_queue:retry"
        self.DEAD_LETTER_QUEUE = "task_queue:dead_letter"

    def enqueue_task(
        self,
        task_name: str,
        args: tuple = (),
        kwargs: Dict[str, Any] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3,
        retry_delay: int = 60,
        queue_name: str = None,
    ) -> str:
        """
        Thêm task vào queue

        Args:
            task_name: Tên task cần thực thi
            args: Arguments cho task
            kwargs: Keyword arguments cho task
            priority: Mức độ ưu tiên của task
            max_retries: Số lần retry tối đa
            retry_delay: Thời gian delay giữa các lần retry (seconds)
            queue_name: Tên queue (nếu không có sẽ dùng default)

        Returns:
            Task ID
        """
        try:
            # Create and save task to database
            task = Task.objects.create(
                task_name=task_name,
                args=list(args) if args else [],
                kwargs=kwargs or {},
                queue_name=queue_name or self.queue_name,
                priority=priority,
                max_retries=max_retries,
                retry_delay=retry_delay,
                status=TaskStatus.PENDING,
            )

            # Add task to Redis queue
            queue_key = f"{self.PENDING_QUEUE}:{task.queue_name}"
            task_data = task.to_dict()
            self.redis.zadd(queue_key, {json.dumps(task_data): priority})

            logger.info(f"Task {task.id} added to queue {task.queue_name}")
            return str(task.id)

        except Exception as e:
            logger.error(f"Failed to add task to queue: {e}")
            raise

    def dequeue_task(self, worker_id: str) -> Optional[Task]:
        """
        Lấy task tiếp theo từ queue theo thứ tự ưu tiên

        Returns:
            Task object hoặc None nếu không có task
        """
        if not worker_id:
            worker_id = f"worker_{uuid.uuid4().hex[:8]}"

        queue_key = f"{self.PENDING_QUEUE}:{self.queue_name}"
        processing_key = f"{self.PROCESSING_QUEUE}:{worker_id}"
        with self.redis.pipeline() as pipe:
            while True:
                try:
                    pipe.watch(queue_key)
                    # Get highest priority task (highest score first)
                    tasks = pipe.zrevrange(queue_key, 0, 0, withscores=True)
                    if not tasks:
                        pipe.unwatch()
                        return None

                    task_json, score = tasks[0]
                    task_data = json.loads(task_json)
                    task_id = task_data["task_id"]

                    # Start transaction
                    pipe.multi()

                    # Move task from pending to processing
                    pipe.zrem(queue_key, task_json)

                    # Add to processing queue with timestamp
                    processing_data = {
                        **task_data,
                        "worker_id": worker_id,
                        "started_at": timezone.now().isoformat(),
                    }
                    pipe.hset(processing_key, task_id, json.dumps(processing_data))
                    pipe.expire(processing_key, 3600)

                    pipe.execute()

                    try:
                        # Update task in db
                        task = Task.objects.get(id=task_id)
                        task.mark_as_processing(worker_id)

                        logger.info(
                            f"Task {task_id} started processing by worker {worker_id}"
                        )
                        return processing_data
                    except Exception as e:
                        logger.error(f"Failed to update task {task_id} in db: {e}")
                        return None

                except redis.WatchError:
                    logger.warning(f"Task {task_id} was modified by another worker")
                    continue
                break

    def complete_task(self, task_id: str, worker_id: str, result: Any = None):
        """
        Đánh dấu task đã hoàn thành

        Args:
            task_id: ID của task
            worker_id: ID của worker
            result: Kết quả của task
        """
        try:
            # Remove task from processing queue
            processing_key = f"{self.PROCESSING_QUEUE}:{worker_id}"
            self.redis.hdel(processing_key, task_id)

            # Update task in db
            task = Task.objects.get(id=task_id)
            task.mark_as_completed(result)

            # Add task to completed queue
            completed_key = f"{self.COMPLETED_QUEUE}:{self.queue_name}"
            self.redis.lpush(completed_key, task_id)

            logger.info(f"Task {task_id} completed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to complete task {task_id}: {e}")
            return False

    def fail_task(self, task_id: str, worker_id: str, error_message: str):
        """
        Đánh dấu task thất bại

        Args:
            task_id: ID của task
            error_message: Thông báo lỗi
        """
        try:
            # Remove task from processing queue
            processing_key = f"{self.PROCESSING_QUEUE}:{worker_id}"
            self.redis.hdel(processing_key, task_id)

            # Update task in db
            task = Task.objects.get(id=task_id)
            if task.can_retry():
                task.mark_for_retry()

                retry_data = task.to_dict()
                retry_score = task.next_retry_at.timestamp()
                self.redis.zadd(self.RETRY_QUEUE, {json.dumps(retry_data): retry_score})
                logger.info(
                    f"Task {task_id} scheduled for retry (attempt {task.retry_count}/{task.max_retries})"
                )
            else:
                task.mark_as_failed(error_message)
                task_data = task.to_dict()
                self.redis.lpush(self.DEAD_LETTER_QUEUE, json.dumps(task_data))
                logger.error(f"Task {task_id} failed: {error_message}")

            return True
        except Exception as e:
            logger.error(f"Failed to fail task {task_id}: {e}")
            return False

    def process_retry_queue(self):
        """
        Xử lý retry queue - move các task đã đến thời gian retry về priority queue
        """
        try:
            current_time = timezone.now().timestamp()

            ready_tasks = self.redis.zrangebyscore(
                self.RETRY_QUEUE, 0, current_time, withscores=True
            )
            moved_count = 0
            for task_json, score in ready_tasks:
                try:
                    task_data = json.loads(task_json)
                    task_id = task_data["task_id"]

                    self.redis.zrem(self.RETRY_QUEUE, task_json)

                    queue_key = f"{self.PENDING_QUEUE}:{task_data['queue_name']}"
                    pending_data = {
                        "task_id": task_id,
                        "task_name": task_data["task_name"],
                        "args": task_data["args"],
                        "kwargs": task_data["kwargs"],
                        "priority": task_data["priority"],
                        "queue_name": task_data["queue_name"],
                        "created_at": task_data["created_at"],
                    }
                    self.redis.zadd(
                        queue_key, {json.dumps(pending_data): task_data["priority"]}
                    )

                    # Update task status in db
                    task = Task.objects.get(id=task_id)
                    task.status = TaskStatus.PENDING
                    task.save(update_fields=["status", "updated_at"])

                    moved_count += 1
                    logger.info(
                        f"Task {task_id} moved from retry queue back to pending"
                    )
                except Exception as e:
                    logger.error(f"Failed to process retry task {task_id}: {e}")
                    continue

            if moved_count > 0:
                logger.info(
                    f"Moved {moved_count} tasks from retry queue back to pending"
                )

        except Exception as e:
            logger.error(f"Failed to process retry queue: {e}")
            return False

    def get_queue_stats(self) -> Dict[str, int]:
        """
        Lấy thống kê về queue

        Returns:
            Dictionary chứa số lượng task trong các queue
        """
        try:
            queue_keys = f"{self.PENDING_QUEUE}:{self.queue_name}"
            stats = {
                "pending": self.redis.zcard(queue_keys),
                "retry": self.redis.zcard(self.RETRY_QUEUE),
                "completed": self.redis.llen(f"{self.COMPLETED_QUEUE}:{self.queue_name}"),
                "dead_letter": self.redis.llen(self.DEAD_LETTER_QUEUE),
                "processing": 0,
            }

            # Count processing tasks
            processing_keys = self.redis.keys(f"{self.PROCESSING_QUEUE}:*")
            for key in processing_keys:
                stats["processing"] += self.redis.hlen(key)

            return stats

        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {}


queue_manager = QueueManager()
