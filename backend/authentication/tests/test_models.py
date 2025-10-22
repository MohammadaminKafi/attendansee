import pytest
from django.contrib.auth import get_user_model
from rest_framework import status


User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Test cases for the User model."""
    
    def test_create_user(self):
        """Test creating a regular user."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.check_password('testpass123')
        assert not user.is_staff
        assert not user.is_superuser
        assert user.is_active
    
    def test_create_superuser(self):
        """Test creating an admin/superuser."""
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        assert admin.username == 'admin'
        assert admin.email == 'admin@example.com'
        assert admin.check_password('adminpass123')
        assert admin.is_staff
        assert admin.is_superuser
        assert admin.is_active
    
    def test_user_string_representation(self):
        """Test the string representation of user."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        assert str(user) == 'testuser'
    
    def test_email_uniqueness(self):
        """Test that email must be unique."""
        User.objects.create_user(
            username='user1',
            email='test@example.com',
            password='testpass123'
        )
        
        with pytest.raises(Exception):
            User.objects.create_user(
                username='user2',
                email='test@example.com',
                password='testpass456'
            )
    
    def test_username_uniqueness(self):
        """Test that username must be unique."""
        User.objects.create_user(
            username='testuser',
            email='test1@example.com',
            password='testpass123'
        )
        
        with pytest.raises(Exception):
            User.objects.create_user(
                username='testuser',
                email='test2@example.com',
                password='testpass456'
            )
