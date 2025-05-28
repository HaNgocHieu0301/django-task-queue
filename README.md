# Django Worker with Redis & PostgreSQL

Django project với Redis integration và PostgreSQL database.

## 🚀 Quick Start

### Start with Docker:
```bash
# Start all services (Django, Redis, PostgreSQL)
docker-compose up -d

# Check services status
docker-compose ps
```

### Run Database Migrations:
```bash
# Create new migrations
docker-compose exec django python manage.py makemigrations

# Apply migrations to create tables
docker-compose exec django python manage.py migrate

# Create superuser (optional)
docker-compose exec django python manage.py createsuperuser
```

## 🧪 Testing

### Run Connection (Redis, Postgresql) Tests:

```bash
# Run all Redis tests
docker-compose exec django python manage.py test tests.test_redis_connection

# Run all Database tests
docker-compose exec django python manage.py test tests.test_database_connection -v 2

# Run test model task:
docker-compose exec django python manage.py test tests.test_models -v 2

# Run test API
docker-compose exec django python manage.py test tests.test_api_tasks -v 2

# Run test queue manager
docker-compose exec django python manage.py test tests.test_queue_manager -v 2

```

## 🐳 Docker Services

| Service | Description | External Port | Internal Port |
|---------|-------------|---------------|---------------|
| **django** | Django application | 8000 | 8000 |
| **redis** | Redis cache/message broker | 6380 | 6379 |
| **postgres** | PostgreSQL database | 5433 | 5432 |

## 📁 Project Structure

```
├── api/                        # Django Backend API
│   ├── django_task_queue/      # Main Django project
│   ├── tasks/                  # Django app for task management
│   ├── tests/                  # Comprehensive test suite
│   ├── __init__.py             # API package initialization
│   ├── Dockerfile              # Django container definition
│   ├── requirements.txt        # Python dependencies
│   └── manage.py               # Django management script
├── client/                     # Frontend
├── docker-compose.yaml         # Docker services configuration
└── README.md                   # This file
```