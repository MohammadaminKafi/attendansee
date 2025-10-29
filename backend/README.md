# AttendanSee Backend

Django REST API backend for the AttendanSee attendance tracking application.

## Project Structure

```
backend/
├── attendansee_backend/  # Main Django project settings
├── authentication/       # User authentication app (JWT + Djoser)
├── attendance/          # Attendance tracking app
├── manage.py
└── pyproject.toml
```

## Features

- JWT-based authentication
- Custom user model with admin and regular user levels
- RESTful API using Django REST Framework
- PostgreSQL database
- Comprehensive test coverage with pytest

## Setup Instructions

### 1. Install Dependencies

The project uses `uv` for dependency management:

```bash
cd backend
uv sync
```

### 2. Configure Environment

Copy the example environment file and update it with your settings:

```bash
cp .env.example .env
```

Edit `.env` with your database credentials and other settings.

### 3. Create Database

Create a PostgreSQL database:

```bash
# Using psql
psql -U postgres
CREATE DATABASE attendansee_db;
CREATE USER attendansee_user WITH PASSWORD 'attendansee_user';
GRANT ALL PRIVILEGES ON DATABASE attendansee_db TO attendansee_user;
\q
```

### 4. Run Migrations

```bash
uv run python manage.py makemigrations
uv run python manage.py migrate
```

### 5. Create Superuser

```bash
uv run python manage.py createsuperuser
```

### 6. Run Development Server

```bash
# For local development (WSL/Linux only)
uv run python manage.py runserver

# For WSL with Windows access (bind to all interfaces)
uv run python manage.py runserver 0.0.0.0:8000
```

**Important for WSL users:** When running Django in WSL and accessing from Windows, use `0.0.0.0:8000` to bind to all network interfaces. This makes the server accessible from Windows at `http://localhost:8000/` or `http://<WSL-IP>:8000/`.

The API will be available at:
- From WSL: `http://localhost:8000/` or `http://127.0.0.1:8000/`
- From Windows (when using `0.0.0.0:8000`): `http://localhost:8000/`

## Testing

Run tests with pytest:

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=authentication --cov=attendance

# Run specific test file
uv run pytest authentication/tests/test_authentication.py

# Run with verbose output
uv run pytest -v
```

## API Documentation

### Authentication Endpoints

- `POST /api/auth/jwt/create/` - Login (obtain JWT token)
- `POST /api/auth/jwt/refresh/` - Refresh access token
- `POST /api/auth/jwt/verify/` - Verify token validity
- `POST /api/auth/users/` - Register new user
- `GET /api/auth/users/me/` - Get current user details
- `PATCH /api/auth/users/me/` - Update current user
- `POST /api/auth/users/set_password/` - Change password
- `GET /api/auth/users/` - List all users (admin only)

### Admin Panel

Access Django admin at `http://localhost:8000/admin/`

## Technology Stack

- **Django 5.2.7** - Web framework
- **Django REST Framework 3.16.1** - REST API
- **djangorestframework-simplejwt 5.5.1** - JWT authentication
- **Djoser 2.3.3** - User management
- **PostgreSQL** - Database
- **pytest 8.4.2** - Testing framework
- **pytest-django 4.11.1** - Django pytest plugin
- **pytest-cov 7.0.0** - Coverage reporting

## Development

### Code Style

Follow PEP 8 guidelines for Python code.

### Running Migrations

After model changes:

```bash
uv run python manage.py makemigrations
uv run python manage.py migrate
```

### Collecting Static Files

```bash
uv run python manage.py collectstatic
```

## License

[Add your license here]
