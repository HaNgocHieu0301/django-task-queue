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
docker-compose exec django python manage.py test tests.test_database_connection

# Run both test files
docker-compose exec django python manage.py test tests.test_redis_connection tests.test_database_connection
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
│   │   ├── settings.py         # Django settings with PostgreSQL support
│   │   ├── urls.py             # URL configuration
│   │   ├── wsgi.py             # WSGI configuration
│   │   └── redis_client.py     # Redis client wrapper
│   ├── tasks/                  # Django app
│   │   ├── models.py           # Database models
│   │   ├── views.py            # API views
│   │   └── urls.py             # App URLs
│   ├── tests/                  # Test files
│   │   ├── __init__.py         # Tests package
│   │   ├── test_redis_connection.py    # Redis connection tests
│   │   └── test_database_connection.py # Database connection tests
│   ├── Dockerfile              # Django container definition
│   ├── requirements.txt        # Python dependencies
│   └── manage.py               # Django management script
├── client/                     # Frontend (React/Vue/etc.)
├── docker-compose.yaml         # Docker services configuration
└── README.md                   # This file
```