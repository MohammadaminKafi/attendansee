# Authentication App

This Django app handles user authentication for the AttendanSee application using JWT tokens and Djoser.

## Features

- Custom User model extending Django's AbstractUser
- JWT-based authentication using `djangorestframework-simplejwt`
- User management endpoints via Djoser
- Two user levels:
  - **Admin**: Full access to Django admin panel (`is_staff=True`)
  - **Regular User**: Standard user access (`is_staff=False`)

## API Endpoints

### Authentication
- `POST /api/auth/jwt/create/` - Obtain JWT token (login)
- `POST /api/auth/jwt/refresh/` - Refresh JWT token
- `POST /api/auth/jwt/verify/` - Verify JWT token

### User Management
- `POST /api/auth/users/` - Register new user
- `GET /api/auth/users/me/` - Get current user details
- `PUT /api/auth/users/me/` - Update current user
- `PATCH /api/auth/users/me/` - Partially update current user
- `DELETE /api/auth/users/me/` - Delete current user
- `POST /api/auth/users/set_password/` - Change password
- `GET /api/auth/users/` - List all users (admin only)

## User Model

The custom `User` model includes:
- `username` (unique)
- `email` (unique)
- `first_name`
- `last_name`
- `is_staff` (determines admin access)
- Standard Django user fields (password, is_active, date_joined, etc.)

## Tests

Tests are located in `authentication/tests/` and cover:
- User model creation and validation
- JWT authentication flow
- User registration
- User permissions
- Password management
- User activation/deactivation

Run tests with pytest:
```bash
pytest authentication/tests/
```

## Configuration

Key settings in `settings.py`:
- `AUTH_USER_MODEL = 'authentication.User'` - Custom user model
- `SIMPLE_JWT` - JWT token configuration
- `DJOSER` - User management settings
- `REST_FRAMEWORK` - API configuration
