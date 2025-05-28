import pytest
import os
from django.test import TestCase
from django.db import connection, connections
from django.conf import settings
from django.core.management import call_command
from django.contrib.auth.models import User
from django.db.utils import OperationalError


class TestDatabaseConnection(TestCase):
    """
    Test cases để kiểm tra kết nối database và các chức năng cơ bản
    """

    def test_database_connection_successful(self):
        """
        Test: Kiểm tra kết nối database thành công
        """
        try:
            # Test connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                self.assertEqual(result[0], 1, "Database connection should return 1")
        except OperationalError as e:
            self.fail(f"Database connection failed: {e}")

    def test_database_configuration(self):
        """
        Test: Kiểm tra cấu hình database
        """
        db_config = settings.DATABASES['default']
        
        # Kiểm tra database engine
        self.assertIsNotNone(db_config['ENGINE'], "Database engine should be configured")
        
        # Kiểm tra database name
        self.assertIsNotNone(db_config['NAME'], "Database name should be configured")
        
        # Log database info
        print(f"Database Engine: {db_config['ENGINE']}")
        print(f"Database Name: {db_config['NAME']}")
        
        if 'postgresql' in db_config['ENGINE']:
            print(f"PostgreSQL Host: {db_config.get('HOST', 'Not set')}")
            print(f"PostgreSQL Port: {db_config.get('PORT', 'Not set')}")
            print(f"PostgreSQL User: {db_config.get('USER', 'Not set')}")

    def test_database_operations(self):
        """
        Test: Kiểm tra các thao tác cơ bản với database
        """
        # Test CREATE
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        self.assertIsNotNone(user.id, "User should be created with ID")
        
        # Test READ
        retrieved_user = User.objects.get(username='testuser')
        self.assertEqual(retrieved_user.email, 'test@example.com', "User email should match")
        
        # Test UPDATE
        retrieved_user.email = 'updated@example.com'
        retrieved_user.save()
        
        updated_user = User.objects.get(username='testuser')
        self.assertEqual(updated_user.email, 'updated@example.com', "User email should be updated")
        
        # Test DELETE
        user_id = updated_user.id
        updated_user.delete()
        
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(id=user_id)

    def test_database_migrations(self):
        """
        Test: Kiểm tra migrations có thể chạy
        """
        try:
            # Test showmigrations command
            call_command('showmigrations', verbosity=0)
            
            # Test migrate command (dry run)
            call_command('migrate', verbosity=0, run_syncdb=True)
            
        except Exception as e:
            self.fail(f"Migration test failed: {e}")

    def test_database_environment_variables(self):
        """
        Test: Kiểm tra environment variables cho database
        """
        # Kiểm tra PostgreSQL environment variables nếu có
        postgres_host = os.getenv('POSTGRES_HOST')
        if postgres_host:
            self.assertEqual(postgres_host, 'postgres', "POSTGRES_HOST should be 'postgres' in Docker")
            
            postgres_db = os.getenv('POSTGRES_DB')
            self.assertIsNotNone(postgres_db, "POSTGRES_DB should be set")
            
            postgres_user = os.getenv('POSTGRES_USER')
            self.assertIsNotNone(postgres_user, "POSTGRES_USER should be set")
            
            postgres_password = os.getenv('POSTGRES_PASSWORD')
            self.assertIsNotNone(postgres_password, "POSTGRES_PASSWORD should be set")

    def test_database_raw_sql(self):
        """
        Test: Kiểm tra thực thi raw SQL
        """
        with connection.cursor() as cursor:
            # Test basic SQL query
            cursor.execute("SELECT version()")
            version = cursor.fetchone()
            self.assertIsNotNone(version, "Database version should be returned")
            
            # Test table creation and operations
            cursor.execute("""
                CREATE TEMPORARY TABLE test_table (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert test data
            cursor.execute(
                "INSERT INTO test_table (name) VALUES (%s)",
                ['Test Name']
            )
            
            # Query test data
            cursor.execute("SELECT name FROM test_table WHERE name = %s", ['Test Name'])
            result = cursor.fetchone()
            self.assertEqual(result[0], 'Test Name', "Raw SQL operations should work")


@pytest.mark.django_db
class TestDatabaseConnectionPytest:
    """
    Test cases sử dụng pytest để kiểm tra database connection
    """

    def test_database_ping(self):
        """
        Test: Database ping thành công
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                assert result[0] == 1, "Database ping should return 1"
        except Exception as e:
            pytest.fail(f"Database ping failed: {e}")

    def test_database_info(self):
        """
        Test: Lấy thông tin database
        """
        db_config = settings.DATABASES['default']
        
        assert db_config['ENGINE'] is not None, "Database engine should be configured"
        assert db_config['NAME'] is not None, "Database name should be configured"
        
        # Print database info for debugging
        print(f"\nDatabase Configuration:")
        print(f"  Engine: {db_config['ENGINE']}")
        print(f"  Name: {db_config['NAME']}")
        
        if 'postgresql' in db_config['ENGINE']:
            print(f"  Host: {db_config.get('HOST', 'localhost')}")
            print(f"  Port: {db_config.get('PORT', '5432')}")
            print(f"  User: {db_config.get('USER', 'Not set')}")

    def test_database_crud_operations(self):
        """
        Test: CRUD operations với database
        """
        # Create
        user = User.objects.create_user(
            username='pytest_user',
            email='pytest@example.com',
            password='testpass123'
        )
        assert user.id is not None, "User should be created with ID"
        
        # Read
        retrieved_user = User.objects.get(username='pytest_user')
        assert retrieved_user.email == 'pytest@example.com', "Email should match"
        
        # Update
        retrieved_user.email = 'pytest_updated@example.com'
        retrieved_user.save()
        
        updated_user = User.objects.get(username='pytest_user')
        assert updated_user.email == 'pytest_updated@example.com', "Email should be updated"
        
        # Delete
        user_id = updated_user.id
        updated_user.delete()
        
        with pytest.raises(User.DoesNotExist):
            User.objects.get(id=user_id)


class TestDatabaseIntegration(TestCase):
    """
    Integration tests cho database trong môi trường Docker
    """

    def test_database_connection_in_docker_environment(self):
        """
        Test: Kiểm tra kết nối database trong môi trường Docker
        """
        # Kiểm tra environment variables
        postgres_host = os.getenv('POSTGRES_HOST')
        database_url = os.getenv('DATABASE_URL')
        
        if postgres_host or database_url:
            # Đang chạy trong Docker với PostgreSQL
            db_config = settings.DATABASES['default']
            self.assertIn('postgresql', db_config['ENGINE'], "Should use PostgreSQL in Docker")
            
            # Test connection
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT version()")
                    version = cursor.fetchone()[0]
                    self.assertIn('PostgreSQL', version, "Should be connected to PostgreSQL")
            except Exception as e:
                self.fail(f"PostgreSQL connection failed in Docker: {e}")
        else:
            # Chạy local với SQLite
            db_config = settings.DATABASES['default']
            self.assertIn('sqlite', db_config['ENGINE'], "Should use SQLite for local development")

    def test_database_performance(self):
        """
        Test: Kiểm tra hiệu suất database cơ bản
        """
        import time
        
        # Test bulk create performance
        start_time = time.time()
        
        users = []
        for i in range(100):
            users.append(User(
                username=f'perftest_user_{i}',
                email=f'perftest_{i}@example.com'
            ))
        
        User.objects.bulk_create(users)
        
        create_time = time.time() - start_time
        
        # Test bulk query performance
        start_time = time.time()
        user_count = User.objects.filter(username__startswith='perftest_').count()
        query_time = time.time() - start_time
        
        self.assertEqual(user_count, 100, "Should create 100 test users")
        self.assertLess(create_time, 5.0, "Bulk create should complete within 5 seconds")
        self.assertLess(query_time, 1.0, "Query should complete within 1 second")
        
        # Cleanup
        User.objects.filter(username__startswith='perftest_').delete() 