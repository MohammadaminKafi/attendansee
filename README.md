# AttendanSee - Attendance Management System

A modern attendance management system using facial recognition technology. Professors can take images during class sessions, and the system automatically detects and identifies students using face recognition.

## 🎯 Project Overview

AttendanSee is a full-stack application that simplifies classroom attendance tracking through automated face detection and recognition. It consists of:

- **Backend**: Django REST API with comprehensive attendance management
- **Frontend**: React SPA with professional dark theme UI
- **Core**: Python-based face recognition engine (in development)

## 📁 Project Structure

```
AttendanSee/
├── backend/                 # Django REST API
│   ├── attendansee_backend/ # Project settings
│   ├── authentication/      # User authentication
│   ├── attendance/          # Attendance management
│   └── docs/               # Backend documentation
├── frontend/                # React frontend
│   ├── src/                # Source code
│   ├── public/             # Static assets
│   └── docs/               # Frontend documentation
└── core/                   # Face recognition engine
    └── face/               # Face detection/recognition modules
```

## ✨ Features

### Currently Implemented

#### Backend (Django REST API)
- ✅ JWT-based authentication with token refresh
- ✅ User management (Admin & Regular users)
- ✅ Class management (CRUD operations)
- ✅ Student management with bulk upload
- ✅ Session management
- ✅ Image upload and processing
- ✅ Face crop detection and storage
- ✅ Attendance tracking
- ✅ Comprehensive test coverage
- ✅ API documentation (Swagger/ReDoc)

#### Frontend (React + TypeScript)
- ✅ Professional dark theme UI
- ✅ JWT authentication with auto-refresh
- ✅ Class management interface
- ✅ Responsive design
- ✅ Protected routes
- ✅ Error handling
- ✅ Docker support

### Planned Features

- 🔜 Student management UI
- 🔜 Session management UI
- 🔜 Image upload interface
- 🔜 Face recognition integration
- 🔜 Attendance reports and analytics
- 🔜 User profile management
- 🔜 Bulk operations

## 🚀 Quick Start

### Prerequisites

- **Backend**: Python 3.10+, PostgreSQL 13+
- **Frontend**: Node.js 18+, npm
- **Docker**: Docker & Docker Compose (optional)

### Backend Setup

```bash
cd backend

# Install dependencies (using uv)
uv sync

# Configure database
# Create PostgreSQL database and user (see backend/README.md)

# Run migrations
uv run python manage.py migrate

# Create superuser
uv run python manage.py createsuperuser

# Start server
uv run python manage.py runserver
```

Backend runs at `http://localhost:8000`

**API Documentation**: `http://localhost:8000/swagger/`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env to set VITE_API_BASE_URL

# Start development server
npm run dev
```

Frontend runs at `http://localhost:3000`

### Docker Setup (Recommended)

```bash
# Frontend only
cd frontend
docker-compose up -d

# Access at http://localhost:3000
```

## 📚 Documentation

### Backend
- [Backend README](./backend/README.md) - Complete setup and API guide
- [Admin Implementation](./backend/docs/ADMIN_IMPLEMENTATION_SUMMARY.md)
- [Admin Quick Reference](./backend/docs/ADMIN_QUICK_REFERENCE.md)

### Frontend
- [Frontend README](./frontend/README.md) - Complete setup and features
- [Quick Start Guide](./frontend/docs/QUICKSTART.md) - Get started in 5 minutes
- [Architecture](./frontend/docs/ARCHITECTURE.md) - Design and patterns
- [Implementation Summary](./frontend/docs/IMPLEMENTATION_SUMMARY.md)

## 🏗️ Architecture

### Backend Architecture

```
Django REST Framework
├── Authentication App (JWT + Djoser)
├── Attendance App (Core models)
└── PostgreSQL Database
```

**Key Technologies:**
- Django 5.2.7
- Django REST Framework 3.16.1
- PostgreSQL
- JWT Authentication
- pytest for testing

### Frontend Architecture

```
React SPA
├── Authentication Layer (Context + JWT)
├── Component Layer (UI components)
├── Service Layer (API client)
└── Routing Layer (React Router)
```

**Key Technologies:**
- React 18
- TypeScript
- Vite
- TailwindCSS
- Axios
- Docker + Nginx

### Data Model

```
User
├── Classes (owns)
    ├── Students (enrolled)
    └── Sessions (conducted)
        ├── Images (uploaded)
            └── FaceCrops (detected)
                └── Student (identified - optional)
```

## 🔐 Authentication Flow

1. User logs in with username/password
2. Backend validates and returns JWT tokens (access + refresh)
3. Frontend stores tokens in localStorage
4. Access token sent with each API request
5. On 401 error, frontend attempts token refresh
6. If refresh succeeds, retry original request
7. If refresh fails, redirect to login

## 📊 Current Capabilities

### For Professors

1. **Create and manage classes**
   - Add class name, description
   - Set active/inactive status
   - View student and session counts

2. **Manage students**
   - Add students individually
   - Bulk upload via CSV/Excel
   - View student attendance

3. **Conduct sessions**
   - Create session for a class
   - Upload multiple images
   - Process images for face detection

4. **Track attendance**
   - View session attendance
   - Generate attendance reports
   - Export data

### For Administrators

- Manage all users
- Access all classes and sessions
- View system-wide statistics
- Django admin panel access

## 🔧 Development

### Backend Development

```bash
cd backend

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=authentication --cov=attendance

# Create migrations
uv run python manage.py makemigrations

# Run migrations
uv run python manage.py migrate
```

### Frontend Development

```bash
cd frontend

# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## 🧪 Testing

### Backend
- Comprehensive test suite with pytest
- ~95% code coverage
- Unit tests for models, serializers, views
- Integration tests for API endpoints

### Frontend
- Manual testing currently
- Ready for unit tests (Jest + React Testing Library)
- Ready for E2E tests (Cypress/Playwright)

## 🚢 Deployment

### Backend
- Deploy with Django production settings
- Use gunicorn/uwsgi
- Configure PostgreSQL
- Set up static file serving

### Frontend
- Build with `npm run build`
- Deploy with Docker (recommended)
- Or serve with any static file server
- Configure environment variables

## 🔒 Security

### Implemented
- JWT authentication
- Token refresh mechanism
- CORS configuration
- SQL injection protection (Django ORM)
- XSS protection (React + Django)
- CSRF protection
- Secure password hashing
- Environment variable configuration

### Best Practices
- No hardcoded secrets
- Environment-based configuration
- Secure token storage
- Protected API endpoints
- Input validation

## 🎨 UI/UX Features

- **Dark Theme**: Professional, easy on the eyes
- **Responsive**: Works on desktop, tablet, mobile
- **Intuitive**: Clear navigation and actions
- **Accessible**: Semantic HTML, keyboard navigation
- **Fast**: Optimized builds, lazy loading
- **Error Handling**: Clear error messages
- **Loading States**: Visual feedback during operations

## 📈 Performance

### Backend
- Database query optimization
- Indexed fields
- Pagination for large datasets
- Efficient serializers

### Frontend
- Code splitting
- Lazy loading (ready)
- Optimized builds (Vite)
- Static asset caching
- Gzip compression (nginx)

## 🛣️ Roadmap

### Phase 1: Core Features ✅
- [x] Backend API
- [x] Authentication
- [x] Class management (backend + frontend)
- [x] Basic UI

### Phase 2: Student & Session Management 🔄
- [ ] Student management UI
- [ ] Session management UI
- [ ] Image upload UI

### Phase 3: Face Recognition Integration
- [ ] Face detection implementation
- [ ] Face recognition model
- [ ] Automated attendance marking

### Phase 4: Analytics & Reporting
- [ ] Attendance reports
- [ ] Statistical analysis
- [ ] Data export
- [ ] Visualizations

### Phase 5: Advanced Features
- [ ] Real-time processing
- [ ] Mobile app
- [ ] Notifications
- [ ] Multi-language support

## 🤝 Contributing

This is a private educational project. For questions or suggestions, please contact the development team.

## 📄 License

[Add your license here]

## 👥 Team

Developed for classroom attendance management with face recognition capabilities.

## 📞 Support

For issues or questions:
1. Check the documentation in respective README files
2. Review the API documentation at `/swagger/`
3. Contact the development team

---

## Quick Links

- **Backend API Docs**: http://localhost:8000/swagger/
- **Backend Admin**: http://localhost:8000/admin/
- **Frontend App**: http://localhost:3000
- **Backend Repo**: [./backend/](./backend/)
- **Frontend Repo**: [./frontend/](./frontend/)

---

**Built with ❤️ for better classroom management**
