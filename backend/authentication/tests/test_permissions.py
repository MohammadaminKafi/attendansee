import pytest
from django.contrib.auth import get_user_model
from rest_framework import status


User = get_user_model()


@pytest.mark.django_db
class TestUserPermissions:
    """Test cases for user permission levels."""
    
    def test_regular_user_is_not_staff(self, regular_user):
        """Test that regular user is not staff."""
        assert not regular_user.is_staff
        assert not regular_user.is_superuser
    
    def test_admin_user_is_staff(self, admin_user):
        """Test that admin user is staff."""
        assert admin_user.is_staff
        assert admin_user.is_superuser
    
    def test_regular_user_cannot_access_admin(self, regular_user):
        """Test that regular user cannot access Django admin."""
        assert not regular_user.has_perm('admin.can_access_admin')
    
    def test_admin_user_can_access_admin(self, admin_user):
        """Test that admin user can access Django admin."""
        # Admin users with is_staff=True can access Django admin
        assert admin_user.is_staff


@pytest.mark.django_db
class TestUserActivation:
    """Test cases for user activation status."""
    
    def test_new_user_is_active(self, regular_user):
        """Test that new user is active by default."""
        assert regular_user.is_active
    
    def test_deactivate_user(self, regular_user):
        """Test deactivating a user."""
        regular_user.is_active = False
        regular_user.save()
        
        regular_user.refresh_from_db()
        assert not regular_user.is_active
    
    def test_inactive_user_cannot_login(self, api_client, regular_user):
        """Test that inactive user cannot obtain JWT token."""
        from django.urls import reverse
        
        # Deactivate user
        regular_user.is_active = False
        regular_user.save()
        
        url = reverse('authentication:jwt-create')
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
