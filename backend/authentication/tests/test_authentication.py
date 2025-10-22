import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from django.urls import reverse


User = get_user_model()


@pytest.mark.django_db
class TestUserRegistration:
    """Test cases for user registration endpoint."""
    
    def test_register_user_success(self, api_client):
        """Test successful user registration."""
        url = '/api/auth/users/'
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            're_password': 'newpass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'id' in response.data
        assert response.data['username'] == 'newuser'
        assert response.data['email'] == 'newuser@example.com'
        assert 'password' not in response.data
        
        # Verify user was created in database
        user = User.objects.get(username='newuser')
        assert user.email == 'newuser@example.com'
        assert user.check_password('newpass123')
    
    def test_register_user_without_email(self, api_client):
        """Test registration fails without email."""
        url = '/api/auth/users/'
        data = {
            'username': 'newuser',
            'password': 'newpass123'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_register_user_with_duplicate_username(self, api_client, regular_user):
        """Test registration fails with duplicate username."""
        url = '/api/auth/users/'
        data = {
            'username': regular_user.username,
            'email': 'different@example.com',
            'password': 'newpass123'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_register_user_with_duplicate_email(self, api_client, regular_user):
        """Test registration fails with duplicate email."""
        url = '/api/auth/users/'
        data = {
            'username': 'differentuser',
            'email': regular_user.email,
            'password': 'newpass123'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_register_user_with_weak_password(self, api_client):
        """Test registration fails with weak password."""
        url = '/api/auth/users/'
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': '123'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestJWTAuthentication:
    """Test cases for JWT authentication."""
    
    def test_obtain_jwt_token(self, api_client, regular_user):
        """Test obtaining JWT token with valid credentials."""
        url = reverse('authentication:jwt-create')
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
    
    def test_obtain_jwt_token_invalid_credentials(self, api_client, regular_user):
        """Test obtaining JWT token with invalid credentials."""
        url = reverse('authentication:jwt-create')
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_jwt_token(self, api_client, regular_user):
        """Test refreshing JWT token."""
        # First, obtain tokens
        login_url = reverse('authentication:jwt-create')
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        login_response = api_client.post(login_url, login_data, format='json')
        refresh_token = login_response.data['refresh']
        
        # Now refresh the token
        refresh_url = reverse('authentication:jwt-refresh')
        refresh_data = {
            'refresh': refresh_token
        }
        
        response = api_client.post(refresh_url, refresh_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
    
    def test_verify_jwt_token(self, api_client, regular_user):
        """Test verifying JWT token."""
        # First, obtain tokens
        login_url = reverse('authentication:jwt-create')
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        login_response = api_client.post(login_url, login_data, format='json')
        access_token = login_response.data['access']
        
        # Now verify the token
        verify_url = reverse('authentication:jwt-verify')
        verify_data = {
            'token': access_token
        }
        
        response = api_client.post(verify_url, verify_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestUserEndpoints:
    """Test cases for user management endpoints."""
    
    def test_get_current_user(self, authenticated_client, regular_user):
        """Test getting current authenticated user details."""
        url = '/api/auth/users/me/'
        
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == regular_user.username
        assert response.data['email'] == regular_user.email
        assert response.data['is_staff'] == regular_user.is_staff
    
    def test_get_current_user_unauthenticated(self, api_client):
        """Test getting current user without authentication."""
        url = '/api/auth/users/me/'
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_update_current_user(self, authenticated_client, regular_user):
        """Test updating current user details."""
        url = '/api/auth/users/me/'
        data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'Updated'
        assert response.data['last_name'] == 'Name'
        
        # Verify changes in database
        regular_user.refresh_from_db()
        assert regular_user.first_name == 'Updated'
        assert regular_user.last_name == 'Name'
    
    def test_list_users_as_admin(self, admin_authenticated_client, regular_user, admin_user):
        """Test that admin can list all users."""
        url = '/api/auth/users/'
        
        response = admin_authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 2
    
    def test_list_users_as_regular_user(self, authenticated_client):
        """Test that regular user cannot list all users."""
        url = '/api/auth/users/'
        
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_change_password(self, authenticated_client, regular_user):
        """Test changing user password."""
        url = '/api/auth/users/set_password/'
        data = {
            'current_password': 'testpass123',
            'new_password': 'newtestpass456',
            're_new_password': 'newtestpass456'
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify password was changed
        regular_user.refresh_from_db()
        assert regular_user.check_password('newtestpass456')
    
    def test_change_password_with_wrong_current_password(self, authenticated_client):
        """Test changing password with incorrect current password."""
        url = '/api/auth/users/set_password/'
        data = {
            'current_password': 'wrongpassword',
            'new_password': 'newtestpass456'
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
