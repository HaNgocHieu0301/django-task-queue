# Django Task Queue System

A custom task queue system built with Django without using Celery or third-party task queue libraries. The system uses Redis and PostgreSQL for queue storage and management.

## 🚀 Features

- **Worker**: Background process to execute tasks
- **Task Queue**: Store and manage pending tasks using Redis and PostgreSQL
- **Producer API**: Django API endpoints to add tasks to queue
- **Retry Mechanism**: Support retry when tasks fail
- **Multiple Workers**: Support running multiple workers concurrently
- **Priority Queue**: Support task priority (HIGH, NORMAL, LOW)
- **Task Registry**: Automatic registration and management of task functions
- **Monitoring**: API to monitor task status and queue statistics

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Django API    │    │   Redis Queue   │    │     Worker      │
│                 │    │                 │    │                 │
│ - Create Tasks  │───▶│ - Task Storage  │───▶│ - Process Tasks │
│ - Monitor Tasks │    │ - Priority Queue│    │ - Retry Failed  │
│ - Queue Stats   │    │ - Retry Queue   │    │ - Update Status │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                                              │
         │              ┌─────────────────┐             │
         └─────────────▶│   PostgreSQL    │◀────────────┘
                        │                 │
                        │ - Task Metadata │
                        │ - Task Results  │
                        │ - Task History  │
                        └─────────────────┘
```

## 📦 Installation

### 1. Clone repository

```bash
git clone https://github.com/HaNgocHieu0301/django-task-queue.git
cd django-worker
```

### 2. Run with Docker

```bash
# Build and start all services (Django API + Worker + Redis + PostgreSQL)
docker-compose up -d --build

# Run migrations
docker-compose exec django python manage.py migrate

# Create superuser (optional)
docker-compose exec django python manage.py createsuperuser
```

**Note**: Worker is automatically started with docker-compose and will process tasks from the `default` queue.

### 3. Check services

- Django API: http://localhost:8000
- Frontend (if running locally): http://localhost:5173
- Redis: localhost:6379
- PostgreSQL: localhost:5432
- Worker: Automatically running in background

## 🎯 Usage

### 1. Create Task Functions

Create task functions in `tasks/sample_tasks.py`:

```python
from django_task_queue.task_registry import task_registry

@task_registry.register('my_task')
def my_task_function(arg1, arg2):
    """
    Task function description
    """
    # Process logic
    result = arg1 + arg2
    return result
```

### 2. Create Task via API

```bash
# POST /api/tasks/
curl -X POST http://localhost:8000/api/tasks/ \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "add_numbers",
    "args": [10, 20],
    "priority": "high",
    "max_retries": 3
  }'
```

**The worker will automatically process the task within seconds.**

## 🎨 Frontend (Task Queue Visualizer)

### Run Frontend Locally

The project includes a React frontend with TypeScript and Vite for visualizing and managing tasks.

```bash
# Navigate to client directory
cd client

# Install dependencies
npm install

# Start development server
# Ensure Django API is running: docker-compose up -d --build
npm run dev
```

**Frontend will be available at:** http://localhost:5173

### Frontend Features

- ✅ **Real-time Task Monitoring** - View tasks and their status updates
- ✅ **Task Creation Interface** - Create new tasks through UI
- ✅ **Queue Statistics** - Visual dashboard for queue metrics
- ✅ **Task Filtering** - Filter tasks by status, priority, etc.
- ✅ **Auto-refresh** - Automatically polls for task updates

### Frontend Configuration

The frontend connects to Django API at `http://localhost:8000/api`. 

**API Configuration in `client/constants.ts`:**
```typescript
export const API_BASE_URL = 'http://localhost:8000/api';
export const API_POLL_INTERVAL = 3000; // ms
```

**Make sure Django API is running before starting frontend:**

### 3. Worker Management

**Worker is automatically started with docker-compose**, but you can also run additional workers manually:

```bash
# Run additional worker manually
docker-compose exec django python manage.py run_worker

# Run multiple workers
docker-compose exec django python manage.py run_worker --workers=3

# Run worker for specific queue
docker-compose exec django python manage.py run_worker --queue=high_priority

# Run with options
docker-compose exec django python manage.py run_worker \
  --workers=2 \
  --max-tasks=100 \
  --poll-interval=2 \
  --log-level=INFO
```

**Default worker configuration:**
- Queue: `default`
- Workers: 3 concurrent workers
- Log level: INFO
- Auto-restart: Yes (if worker crashes)

### 4. Monitoring

```bash
# List all tasks
curl http://localhost:8000/api/tasks/

# Filter tasks by status
curl http://localhost:8000/api/tasks/?status=pending
curl http://localhost:8000/api/tasks/?status=success
curl http://localhost:8000/api/tasks/?status=failed
```

## 📋 Management Commands

### List Tasks

```bash
# Display all registered tasks
docker-compose exec django python manage.py list_tasks
```

### Run Worker

```bash
# Run worker with options
docker-compose exec django python manage.py run_worker --help

Options:
  --queue QUEUE         Queue name (default: default)
  --workers WORKERS     Number of workers (default: 1)
  --worker-id ID        Worker ID (for single worker)
  --max-tasks N         Max tasks per worker run
  --poll-interval N     Polling interval in seconds
  --log-level LEVEL     Log level (DEBUG, INFO, WARNING, ERROR)
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
docker-compose exec django python manage.py test

# Run specific test modules
docker-compose exec django python manage.py test tests.test_task_registry
docker-compose exec django python manage.py test tests.test_worker
docker-compose exec django python manage.py test tests.test_integration
```

### Demo Script

```bash
# Run demo to see system in action
docker-compose exec django python demo_task_queue.py
```

## 📊 API Endpoints

### Tasks API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/tasks/` | Create new task |
| GET | `/api/tasks/` | List tasks with filtering |

### Task Creation Payload

```json
{
  "task_name": "string",           // Required: Task function name
  "args": [],                      // Optional: Arguments array
  "kwargs": {},                    // Optional: Keyword arguments
  "priority": "high|normal|low",   // Optional: Task priority
  "max_retries": 3,               // Optional: Max retry attempts
  "retry_delay": 60,              // Optional: Retry delay in seconds
  "timeout": 300,                 // Optional: Task timeout in seconds
  "queue_name": "string"          // Optional: Queue name
}
```

### Response Format

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "task_name": "string",
    "status": "pending|processing|success|failed|retry",
    "args": [],
    "kwargs": {},
    "priority": 1,
    "result": null,
    "error_message": null,
    "retry_count": 0,
    "max_retries": 3,
    "created_at": "datetime",
    "started_at": "datetime",
    "completed_at": "datetime",
    "next_retry_at": "datetime"
  }
}
```

## 📄 Configuration

### Docker Compose Services

The system includes 4 services:

```yaml
services:
  django:          # Django API server
  worker-default:  # Task worker (auto-started)
  redis:          # Message broker
  postgres:       # Database
```

**Worker service configuration:**
```yaml
worker-default:
  command: python manage.py run_worker --queue=default --workers=3 --log-level=INFO
  restart: unless-stopped  # Auto-restart on failure
  depends_on: [redis, postgres, django]
```


## 🔄 Task Lifecycle

```
┌─────────┐    ┌────────────┐    ┌─────────┐    ┌─────────┐
│ PENDING │───▶│ PROCESSING │───▶│ SUCCESS │    │  RETRY  │
└─────────┘    └────────────┘    └─────────┘    └─────────┘
                      │                              │
                      │          ┌─────────┐         │
                      └─────────▶│ FAILED  │◀────────┘
                                 └─────────┘
```

1. **PENDING**: Task created and waiting for processing
2. **PROCESSING**: Worker is processing the task
3. **SUCCESS**: Task completed successfully
4. **FAILED**: Task failed (exhausted retry attempts)
5. **RETRY**: Task failed and waiting for retry

## 📞 Support

If you have issues or questions, please create an issue in the repository.

---