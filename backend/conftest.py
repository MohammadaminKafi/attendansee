"""
Root conftest.py for pytest configuration.
This file is loaded before any test apps' conftest.py files.
"""
import pytest
from django.db import connection


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Override django_db_setup to enable pgvector BEFORE migrations run.
    
    This is critical because the migration tries to add a vector field,
    which requires the vector type to exist in PostgreSQL.
    """
    with django_db_blocker.unblock():
        with connection.cursor() as cursor:
            # Create extension before migrations
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

