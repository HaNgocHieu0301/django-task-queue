#!/usr/bin/env python
"""
Demo script to test the entire Django Task Queue system

Run this script to see the system in action:
python demo_task_queue.py
"""

import os
import sys
import django
import time
import threading
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_task_queue.settings')
django.setup()

from django_task_queue.queue_manager import QueueManager
from django_task_queue.worker import Worker
from tasks.models import Task, TaskStatus, TaskPriority


def demo_basic_task_processing():
    """Basic demo: create tasks and process with worker"""
    print("=" * 60)
    print("DEMO 1: Basic Task Processing")
    print("=" * 60)
    
    # 1. Create queue manager
    queue_manager = QueueManager("demo_queue")
    
    # 2. Enqueue some tasks
    print("\n📝 Enqueuing tasks...")
    
    task_ids = []
    
    # Addition task
    task_id1 = queue_manager.enqueue_task(
        task_name="add_numbers",
        args=[10, 20],
        priority=TaskPriority.HIGH,
        queue_name="demo_queue"
    )
    task_ids.append(task_id1)
    print(f"✅ Added task: add_numbers(10, 20) - ID: {task_id1}")
    
    # Multiplication task
    task_id2 = queue_manager.enqueue_task(
        task_name="multiply_numbers",
        args=[5, 6],
        priority=TaskPriority.NORMAL,
        queue_name="demo_queue"
    )
    task_ids.append(task_id2)
    print(f"✅ Added task: multiply_numbers(5, 6) - ID: {task_id2}")
    
    # Data processing task
    task_id3 = queue_manager.enqueue_task(
        task_name="process_data",
        args=[[1, 2, 3, 4, 5]],
        kwargs={"operation": "sum"},
        priority=TaskPriority.LOW,
        queue_name="demo_queue"
    )
    task_ids.append(task_id3)
    print(f"✅ Added task: process_data([1,2,3,4,5], operation='sum') - ID: {task_id3}")
    
    # 3. Display queue stats
    stats = queue_manager.get_queue_stats()
    print(f"\n📊 Queue stats: {stats}")
    
    # 4. Create and run worker
    print("\n🔧 Starting worker...")
    worker = Worker(
        queue_name="demo_queue",
        worker_id="demo_worker",
        max_tasks_per_run=3,  # Process 3 tasks then stop
        poll_interval=1
    )
    
    # Run worker in separate thread
    worker_thread = threading.Thread(target=worker.start)
    worker_thread.daemon = True
    worker_thread.start()
    
    # Wait for worker to finish processing
    print("⏳ Waiting for worker to process tasks...")
    time.sleep(5)
    
    # Stop worker
    worker.stop()
    
    # 5. Check results
    print("\n📋 Task Results:")
    for task_id in task_ids:
        task = Task.objects.get(id=task_id)
        print(f"Task {task.task_name}: {task.status} - Result: {task.result}")
    
    # 6. Queue stats after processing
    final_stats = queue_manager.get_queue_stats()
    print(f"\n📊 Final queue stats: {final_stats}")


def demo_retry_mechanism():
    """Demo retry mechanism with failing task"""
    print("\n" + "=" * 60)
    print("DEMO 2: Retry Mechanism")
    print("=" * 60)
    
    queue_manager = QueueManager("retry_demo_queue")
    
    # Create failing task
    print("\n📝 Creating failing task...")
    task_id = queue_manager.enqueue_task(
        task_name="failing_task",
        kwargs={"should_fail": True, "error_message": "Demo failure"},
        max_retries=2,
        retry_delay=2,
        queue_name="retry_demo_queue"
    )
    print(f"✅ Added failing task - ID: {task_id}")
    
    # Worker processes task
    print("\n🔧 Starting worker to process failing task...")
    worker = Worker(
        queue_name="retry_demo_queue",
        worker_id="retry_demo_worker",
        max_tasks_per_run=1
    )
    
    # Process first attempt (will fail)
    worker._process_next_task()
    
    # Check task status
    task = Task.objects.get(id=task_id)
    print(f"📋 After first attempt: Status={task.status}, Retry count={task.retry_count}")
    
    # Process retry queue
    print("\n🔄 Processing retry queue...")
    queue_manager.process_retry_queue()
    
    task.refresh_from_db()
    print(f"📋 After retry queue processing: Status={task.status}")


def demo_multiple_workers():
    """Demo multiple workers processing tasks concurrently"""
    print("\n" + "=" * 60)
    print("DEMO 3: Multiple Workers")
    print("=" * 60)
    
    queue_manager = QueueManager("multi_worker_queue")
    
    # Create multiple tasks
    print("\n📝 Creating multiple tasks...")
    task_ids = []
    for i in range(10):
        task_id = queue_manager.enqueue_task(
            task_name="slow_task",
            args=[1],  # Sleep 1 second
            kwargs={"message": f"Task {i+1}"},
            queue_name="multi_worker_queue"
        )
        task_ids.append(task_id)
    
    print(f"✅ Created {len(task_ids)} slow tasks")
    
    # Create multiple workers
    print("\n🔧 Starting 3 workers...")
    workers = []
    threads = []
    
    for i in range(3):
        worker = Worker(
            queue_name="multi_worker_queue",
            worker_id=f"worker_{i+1}",
            max_tasks_per_run=4,  # Each worker processes max 4 tasks
            poll_interval=0.5
        )
        workers.append(worker)
        
        thread = threading.Thread(target=worker.start)
        thread.daemon = True
        thread.start()
        threads.append(thread)
    
    # Wait for workers to process
    print("⏳ Waiting for workers to process tasks...")
    time.sleep(8)
    
    # Stop all workers
    for worker in workers:
        worker.stop()
    
    # Check results
    completed_tasks = Task.objects.filter(
        id__in=task_ids,
        status=TaskStatus.SUCCESS
    ).count()
    
    print(f"\n📊 Results: {completed_tasks}/{len(task_ids)} tasks completed")
    
    # Worker stats
    print("\n👥 Worker Stats:")
    for worker in workers:
        stats = worker.get_stats()
        print(f"  {stats['worker_id']}: {stats['tasks_processed']} tasks processed")


def demo_api_integration():
    """Demo integration with API"""
    print("\n" + "=" * 60)
    print("DEMO 4: API Integration")
    print("=" * 60)
    
    print("\n📝 Creating tasks via QueueManager (simulating API)...")
    
    queue_manager = QueueManager()
    
    # Create tasks like API would do
    api_tasks = [
        {
            "task_name": "send_notification",
            "args": ["user@example.com", "Welcome to our service!"],
            "kwargs": {"notification_type": "email"},
            "priority": TaskPriority.HIGH
        },
        {
            "task_name": "random_task",
            "args": [1, 100],
            "priority": TaskPriority.NORMAL
        },
        {
            "task_name": "process_data",
            "args": [[10, 20, 30, 40, 50]],
            "kwargs": {"operation": "avg"},
            "priority": TaskPriority.LOW
        }
    ]
    
    task_ids = []
    for task_data in api_tasks:
        task_id = queue_manager.enqueue_task(**task_data)
        task_ids.append(task_id)
        print(f"✅ API created task: {task_data['task_name']} - ID: {task_id}")
    
    # Worker processes
    print("\n🔧 Processing tasks with worker...")
    worker = Worker(max_tasks_per_run=len(task_ids))
    
    worker_thread = threading.Thread(target=worker.start)
    worker_thread.daemon = True
    worker_thread.start()
    
    time.sleep(3)
    worker.stop()
    
    # Display results
    print("\n📋 API Task Results:")
    for task_id in task_ids:
        task = Task.objects.get(id=task_id)
        print(f"  {task.task_name}: {task.status} - {task.result}")


def main():
    """Run all demos"""
    print("🚀 Django Task Queue System Demo")
    print("=" * 60)
    
    try:
        # Demo 1: Basic task processing
        demo_basic_task_processing()
        
        # Demo 2: Retry mechanism
        demo_retry_mechanism()
        
        # Demo 3: Multiple workers
        demo_multiple_workers()
        
        # Demo 4: API integration
        demo_api_integration()
        
        print("\n" + "=" * 60)
        print("✅ All demos completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 