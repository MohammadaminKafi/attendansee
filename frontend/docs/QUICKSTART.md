# AttendanSee - Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Prerequisites
- Node.js 18+ installed
- Backend server running at `http://localhost:8000`

### Quick Setup

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Create environment file
cp .env.example .env

# 4. Start development server
npm run dev
```

Open `http://localhost:3000` in your browser and login with your credentials!

## 🐳 Docker Quick Start

```bash
# Navigate to frontend directory
cd frontend

# Start with Docker Compose
docker-compose up -d

# Access at http://localhost:3000
```

## 📋 Default Configuration

The frontend is pre-configured to connect to:
- **Backend API**: `http://localhost:8000/api`

To change this, edit the `.env` file:
```env
VITE_API_BASE_URL=http://your-backend-url/api
```

## 🎯 First Steps After Login

1. **Login** with your credentials
2. **Create a class** using the "Create Class" button
3. **Edit class** details by clicking the edit icon
4. **View statistics** on each class card
5. **Delete a class** with the delete icon (with confirmation)

## 🔧 Common Commands

```bash
# Development
npm run dev          # Start dev server
npm run build        # Build for production
npm run preview      # Preview production build
npm run lint         # Run linter

# Docker
docker-compose up -d      # Start container
docker-compose down       # Stop container
docker-compose logs -f    # View logs
```

## 📱 Features Available

### ✅ Implemented
- Login with JWT authentication
- Class management (Create, Read, Update, Delete)
- Responsive dark theme UI
- Protected routes
- Automatic token refresh

### 🔜 Coming Soon
- Student management
- Session management
- Image upload for face detection
- Attendance reports
- User profile management

## 🐛 Troubleshooting

### Can't login?
- Ensure backend is running
- Check backend URL in `.env`
- Check browser console for errors

### Port 3000 in use?
```bash
# Use different port
PORT=3001 npm run dev
```

### Connection refused?
- Verify backend is running: `http://localhost:8000/api/`
- Check CORS settings in backend
- Ensure `VITE_API_BASE_URL` is correct

## 📚 Learn More

- [Full README](./README.md) - Complete documentation
- [Architecture](./ARCHITECTURE.md) - System design and patterns
- [Backend README](../backend/README.md) - Backend setup guide

## 🤝 Need Help?

Check the full README.md for detailed documentation or contact the development team.

---

**Happy coding! 🎉**
