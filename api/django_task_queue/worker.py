import logging
import signal
import time
import uuid
import threading
from .queue_manager import QueueManager
from .task_registry import task_registry

logger = logging.getLogger(__name__)


class Worker:
    """
    Worker to process tasks from queue.
    """
    
    def __init__(
        self,
        queue_name: str = "default",
        worker_id: str = None,
        poll_interval: int = 1,
        max_tasks_per_run: int = None
    ):
        self.queue_name = queue_name
        self.worker_id = worker_id or f"worker_{uuid.uuid4().hex[:8]}"
        self.poll_interval = poll_interval
        self.max_tasks_per_run = max_tasks_per_run
        
        self.queue_manager = QueueManager(queue_name)
        self.running = False
        self.tasks_processed = 0
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"Worker {self.worker_id} initialized for queue '{queue_name}'")
    
    def _signal_handler(self, signum, frame):
        """
        Handle shutdown signals gracefully.
        """
        logger.info(f"Worker {self.worker_id} received signal {signum}, shutting down...")
        self.stop()
    
    def start(self):
        """
        Start worker loop
        """
        logger.info(f"Worker {self.worker_id} starting...")
        self.running = True
        
        # Start retry queue processor in background
        retry_thread = threading.Thread(target=self._retry_queue_processor, daemon=True)
        retry_thread.start()
        
        try:
            while self.running:
                # Check if we've reached max tasks limit
                if (self.max_tasks_per_run and 
                    self.tasks_processed >= self.max_tasks_per_run):
                    logger.info(f"Worker {self.worker_id} reached max tasks limit ({self.max_tasks_per_run})")
                    break
                
                # Process one task
                if not self._process_next_task():
                    # No tasks available, wait before polling again
                    time.sleep(self.poll_interval)
                
        except Exception as e:
            logger.error(f"Worker {self.worker_id} encountered error: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """
        Stop worker
        """
        if self.running:
            logger.info(f"Worker {self.worker_id} stopping...")
            self.running = False
            logger.info(f"Worker {self.worker_id} processed {self.tasks_processed} tasks")
    
    def _process_next_task(self) -> bool:
        """
        Process next task from queue
        
        Returns:
            True if task is processed, False if no task
        """
        try:
            # Get next task from queue
            task_data = self.queue_manager.dequeue_task(self.worker_id)
            if not task_data:
                return False
            
            task_id = task_data["task_id"]
            task_name = task_data["task_name"]
            args = task_data.get("args", [])
            kwargs = task_data.get("kwargs", {})
            
            logger.info(f"Worker {self.worker_id} processing task {task_id}: {task_name}")
            
            try:
                # Get task function from registry
                task_func = task_registry.get_task(task_name)
                
                # Execute task
                start_time = time.time()
                result = task_func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Mark task as completed
                self.queue_manager.complete_task(task_id, self.worker_id, result)
                
                self.tasks_processed += 1
                logger.info(
                    f"Worker {self.worker_id} completed task {task_id} "
                    f"in {execution_time:.2f}s. Result: {result}"
                )
                
                return True
                
            except KeyError as e:
                # Task function not found
                error_msg = f"Task function not found: {e}"
                logger.error(f"Worker {self.worker_id} failed task {task_id}: {error_msg}")
                self.queue_manager.fail_task(task_id, self.worker_id, error_msg)
                return True
                
            except Exception as e:
                # Task execution failed
                error_msg = f"Task execution failed: {str(e)}"
                logger.error(f"Worker {self.worker_id} failed task {task_id}: {error_msg}")
                self.queue_manager.fail_task(task_id, self.worker_id, error_msg)
                return True
                
        except Exception as e:
            logger.error(f"Worker {self.worker_id} error processing task: {e}")
            return False
    
    def _retry_queue_processor(self):
        """
        Background thread to process retry queue
        """
        logger.info(f"Worker {self.worker_id} started retry queue processor")
        
        while self.running:
            try:
                self.queue_manager.process_retry_queue()
                time.sleep(30)  # Check retry queue every 30 seconds
            except Exception as e:
                logger.error(f"Worker {self.worker_id} retry queue processor error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def get_stats(self) -> dict:
        """
        Get worker statistics
        
        Returns:
            Dictionary containing worker statistics
        """
        queue_stats = self.queue_manager.get_queue_stats()
        
        return {
            "worker_id": self.worker_id,
            "queue_name": self.queue_name,
            "running": self.running,
            "tasks_processed": self.tasks_processed,
            "queue_stats": queue_stats,
            "available_tasks": list(task_registry.list_tasks().keys())
        }


class WorkerPool:
    """
    Pool to manage multiple workers
    """
    
    def __init__(self, num_workers: int = 1, queue_name: str = "default"):
        self.num_workers = num_workers
        self.queue_name = queue_name
        self.workers = []
        self.threads = []
        
        logger.info(f"WorkerPool initialized with {num_workers} workers for queue '{queue_name}'")
    
    def start(self):
        """
        Start all workers
        """
        logger.info(f"Starting {self.num_workers} workers...")
        
        for i in range(self.num_workers):
            worker = Worker(
                queue_name=self.queue_name,
                worker_id=f"worker_{self.queue_name}_{i+1}"
            )
            self.workers.append(worker)
            
            # Start worker in separate thread
            thread = threading.Thread(target=worker.start, daemon=False)
            thread.start()
            self.threads.append(thread)
        
        # Wait for all threads to complete
        for thread in self.threads:
            thread.join()
    
    def stop(self):
        """
        Stop all workers
        """
        logger.info("Stopping all workers...")
        for worker in self.workers:
            worker.stop()
    
    def get_stats(self) -> dict:
        """
        Get statistics of all workers
        """
        return {
            "pool_size": self.num_workers,
            "queue_name": self.queue_name,
            "workers": [worker.get_stats() for worker in self.workers]
        } 