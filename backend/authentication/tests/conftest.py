import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status


User = get_user_model()


@pytest.fixture
def api_client():
    """Fixture to provide an API client for tests."""
    return APIClient()


@pytest.fixture
def regular_user(db):
    """Fixture to create a regular user."""
    return User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def admin_user(db):
    """Fixture to create an admin user."""
    return User.objects.create_user(
        username='adminuser',
        email='admin@example.com',
        password='adminpass123',
        first_name='Admin',
        last_name='User',
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def authenticated_client(api_client, regular_user):
    """Fixture to provide an authenticated API client."""
    api_client.force_authenticate(user=regular_user)
    return api_client


@pytest.fixture
def admin_authenticated_client(api_client, admin_user):
    """Fixture to provide an admin authenticated API client."""
    api_client.force_authenticate(user=admin_user)
    return api_client
