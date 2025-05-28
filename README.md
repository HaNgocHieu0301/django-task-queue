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

# Run test API
docker-compose exec django python manage.py test tasks.tests -v 2

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
│   │   ├── __init__.py         # Package initialization
│   │   ├── settings.py         # Django settings with PostgreSQL support
│   │   ├── urls.py             # URL configuration
│   │   ├── wsgi.py             # WSGI configuration
│   │   ├── asgi.py             # ASGI configuration
│   │   └── redis_client.py     # Redis client wrapper
│   ├── tasks/                  # Django app for task management
│   │   ├── __init__.py         # App package initialization
│   │   ├── models.py           # Task database models
│   │   ├── views.py            # API views (TaskViewSet)
│   │   ├── serializers.py      # DRF serializers
│   │   ├── urls.py             # App URLs
│   │   ├── admin.py            # Django admin configuration
│   │   ├── apps.py             # App configuration
│   │   ├── tests.py            # Task-specific tests
│   │   └── migrations/         # Database migrations
│   ├── tests/                  # Comprehensive test suite
│   │   ├── __init__.py         # Tests package
│   │   ├── apps.py             # Test app configuration
│   │   ├── test_redis_connection.py    # Redis connection tests
│   │   └── test_database_connection.py # Database connection tests
│   ├── __init__.py             # API package initialization
│   ├── Dockerfile              # Django container definition
│   ├── requirements.txt        # Python dependencies
│   └── manage.py               # Django management script
├── client/                     # Frontend
├── docker-compose.yaml         # Docker services configuration
└── README.md                   # This file
```