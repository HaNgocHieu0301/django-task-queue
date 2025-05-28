import os
from django.test import TestCase
from django.db import connection
from django.conf import settings
from django.core.management import call_command
from django.contrib.auth.models import User
from django.db.utils import OperationalError


class TestDatabaseConnection(TestCase):
    """
    Test cases to test database connection and basic functions
    """

    def test_database_connection_successful(self):
        """
        Test: Test database connection successful
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
        Test: Test database configuration
        """
        db_config = settings.DATABASES["default"]

        # Test database engine
        self.assertIsNotNone(
            db_config["ENGINE"], "Database engine should be configured"
        )

        # Test database name
        self.assertIsNotNone(db_config["NAME"], "Database name should be configured")

        # Log database info
        print(f"Database Engine: {db_config['ENGINE']}")
        print(f"Database Name: {db_config['NAME']}")

        if "postgresql" in db_config["ENGINE"]:
            print(f"PostgreSQL Host: {db_config.get('HOST', 'Not set')}")
            print(f"PostgreSQL Port: {db_config.get('PORT', 'Not set')}")
            print(f"PostgreSQL User: {db_config.get('USER', 'Not set')}")

    def test_database_operations(self):
        """
        Test: Test basic database operations
        """
        # Test CREATE
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword123"
        )
        self.assertIsNotNone(user.id, "User should be created with ID")

        # Test READ
        retrieved_user = User.objects.get(username="testuser")
        self.assertEqual(
            retrieved_user.email, "test@example.com", "User email should match"
        )

        # Test UPDATE
        retrieved_user.email = "updated@example.com"
        retrieved_user.save()

        updated_user = User.objects.get(username="testuser")
        self.assertEqual(
            updated_user.email, "updated@example.com", "User email should be updated"
        )

        # Test DELETE
        user_id = updated_user.id
        updated_user.delete()

        with self.assertRaises(User.DoesNotExist):
            User.objects.get(id=user_id)

    def test_database_migrations(self):
        """
        Test: Test database migrations
        """
        try:
            # Test showmigrations command
            call_command("showmigrations", verbosity=0)

            # Test migrate command (dry run)
            call_command("migrate", verbosity=0, run_syncdb=True)

        except Exception as e:
            self.fail(f"Migration test failed: {e}")

    def test_database_environment_variables(self):
        """
        Test: Test database environment variables
        """
        postgres_host = os.getenv("POSTGRES_HOST")
        if postgres_host:
            self.assertEqual(
                postgres_host,
                "postgres",
                "POSTGRES_HOST should be 'postgres' in Docker",
            )

            postgres_db = os.getenv("POSTGRES_DB")
            self.assertIsNotNone(postgres_db, "POSTGRES_DB should be set")

            postgres_user = os.getenv("POSTGRES_USER")
            self.assertIsNotNone(postgres_user, "POSTGRES_USER should be set")

            postgres_password = os.getenv("POSTGRES_PASSWORD")
            self.assertIsNotNone(postgres_password, "POSTGRES_PASSWORD should be set")

    def test_database_raw_sql(self):
        """
        Test: Test raw SQL execution
        """
        with connection.cursor() as cursor:
            # Test basic SQL query
            cursor.execute("SELECT version()")
            version = cursor.fetchone()
            self.assertIsNotNone(version, "Database version should be returned")

            # Test table creation and operations
            cursor.execute(
                """
                CREATE TEMPORARY TABLE test_table (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Insert test data
            cursor.execute("INSERT INTO test_table (name) VALUES (%s)", ["Test Name"])

            # Query test data
            cursor.execute("SELECT name FROM test_table WHERE name = %s", ["Test Name"])
            result = cursor.fetchone()
            self.assertEqual(result[0], "Test Name", "Raw SQL operations should work")
