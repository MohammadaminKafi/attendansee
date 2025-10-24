# AttendanSee Frontend

Professional React frontend for the AttendanSee attendance management system. Built with modern technologies and best practices, featuring a dark theme UI and complete class management functionality.

## 🚀 Features

- **Authentication**: Secure JWT-based authentication with token refresh
- **Class Management**: Full CRUD operations for classes
  - Create new classes
  - Edit existing classes
  - Delete classes with confirmation
  - View class statistics (students and sessions count)
  - **Class Detail Page**: Comprehensive class management (NEW!)
    - Session management with table view and pagination
    - Student management with list view
    - Bulk CSV upload for students
    - Real-time statistics dashboard
- **Modern UI**: Professional dark theme with smooth animations
- **Responsive Design**: Mobile-friendly interface
- **Type Safety**: Full TypeScript support
- **Protected Routes**: Automatic authentication handling

## 🛠️ Tech Stack

- **React 18**: UI framework
- **TypeScript**: Type safety and better DX
- **Vite**: Fast build tool and dev server
- **React Router**: Client-side routing
- **Axios**: HTTP client with interceptors
- **TailwindCSS**: Utility-first CSS framework
- **Lucide React**: Beautiful icon library

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable components
│   │   ├── ui/             # UI components (Button, Input, Modal, Table, etc.)
│   │   ├── tabs/           # Tab components (SessionsTab, StudentsTab)
│   │   ├── Layout.tsx      # Main layout with header
│   │   └── ProtectedRoute.tsx  # Route protection wrapper
│   ├── contexts/           # React contexts
│   │   └── AuthContext.tsx # Authentication state management
│   ├── pages/              # Page components
│   │   ├── LoginPage.tsx   # Login page
│   │   ├── ClassesPage.tsx # Class management page
│   │   └── ClassDetailPage.tsx # Class detail page with sessions/students
│   ├── services/           # API services
│   │   └── api.ts          # Axios instance and API calls
│   ├── types/              # TypeScript types
│   │   └── index.ts        # Shared type definitions
│   ├── utils/              # Utility functions
│   │   └── helpers.ts      # Helper functions
│   ├── App.tsx             # Main app component with routing
│   ├── main.tsx            # Application entry point
│   └── index.css           # Global styles
├── docs/                   # Documentation
│   ├── ARCHITECTURE.md     # Architecture overview
│   ├── IMPLEMENTATION_SUMMARY.md  # Implementation details
│   ├── QUICKSTART.md       # Quick start guide
│   ├── CLASS_DETAIL_PAGE_PLAN.md  # Class detail page design
│   └── CLASS_DETAIL_PAGE.md       # Class detail page docs
├── Dockerfile              # Production Docker image
├── docker-compose.yml      # Docker Compose configuration
├── nginx.conf              # Nginx configuration
├── package.json            # Dependencies and scripts
├── tsconfig.json           # TypeScript configuration
├── tailwind.config.js      # TailwindCSS configuration
└── vite.config.ts          # Vite configuration
```

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running (see backend README)

### Installation

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and set your backend API URL:
   ```env
   VITE_API_BASE_URL=http://localhost:8000/api
   ```

4. **Start development server**
   ```bash
   npm run dev
   ```

   The app will be available at `http://localhost:3000`

### Building for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

### Preview Production Build

```bash
npm run preview
```

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

1. **Build and start the container**
   ```bash
   docker-compose up -d
   ```

   The frontend will be available at `http://localhost:3000`

2. **Stop the container**
   ```bash
   docker-compose down
   ```

### Using Docker Directly

1. **Build the image**
   ```bash
   docker build -t attendansee-frontend .
   ```

2. **Run the container**
   ```bash
   docker run -d \
     -p 3000:80 \
     -e VITE_API_BASE_URL=http://localhost:8000/api \
     --name attendansee-frontend \
     attendansee-frontend
   ```

3. **Stop the container**
   ```bash
   docker stop attendansee-frontend
   docker rm attendansee-frontend
   ```

### Environment Variables

The Docker container supports runtime environment variable configuration:

- `VITE_API_BASE_URL`: Backend API base URL (default: `http://localhost:8000/api`)

## 📱 Pages and Features

### Login Page (`/login`)

- Username and password authentication
- Form validation
- Error handling
- Automatic redirect if already authenticated

### Classes Page (`/classes`)

- **View all classes**: Grid layout with class cards
- **Create class**: Modal form with name, description, and active status
- **Edit class**: Update class information
- **Delete class**: Confirmation modal with warning
- **Navigate to class details**: Click any class card to view details
- **Class cards show**:
  - Class name and status (Active/Inactive)
  - Description (if provided)
  - Number of students
  - Number of sessions
  - Creation date

### Class Detail Page (`/classes/:id`) ⭐ NEW

Comprehensive class management interface with tabbed navigation:

#### Statistics Dashboard
- Total students enrolled
- Total sessions created
- Total images uploaded
- Identified faces count

#### Sessions Tab
- **Table view** with columns: Date, Name, Images, Faces, Status, Actions
- **Pagination** for handling 50+ sessions (10 per page)
- **Search** sessions by name or date
- **Create session**: Name, date, start/end time, notes
- **Edit session**: Update session details
- **Delete session**: Remove with confirmation
- **Status badges**: Visual indicators for processed/pending sessions

#### Students Tab
- **Card list view** with student details
- **Search** by name, student ID, or email
- **Add student**: Manual entry with form validation
- **Edit student**: Update student information
- **Delete student**: Remove with confirmation
- **Bulk CSV upload**:
  - Upload multiple students from CSV file
  - Header row detection option
  - Detailed upload results (created/skipped counts)
  - Error reporting for invalid entries

For more details, see [CLASS_DETAIL_PAGE.md](docs/CLASS_DETAIL_PAGE.md).

## 🎨 UI Components

All components follow a consistent dark theme design:

- **Button**: Primary, secondary, and danger variants with loading states
- **Input**: Form input with label and error display
- **Card**: Container with consistent styling
- **Modal**: Overlay modal with backdrop click and ESC key support
- **LoadingSpinner**: Animated loading indicator
- **Table**: Generic table component with column configuration
- **Pagination**: Page navigation with ellipsis for many pages
- **Tabs**: Tabbed interface for content organization
- **Breadcrumb**: Navigation breadcrumb trail
- **Badge**: Status badges (success, warning, error, info)
- **StatCard**: Statistics display cards with icons

## 🔐 Authentication Flow

1. User enters credentials on login page
2. Frontend sends request to `/api/auth/jwt/create/`
3. Backend returns access and refresh tokens
4. Tokens stored in localStorage
5. Access token added to all subsequent requests
6. On 401 error, automatic token refresh attempted
7. If refresh fails, user redirected to login

## 🌐 API Integration

The frontend integrates with the following backend endpoints:

### Authentication
- `POST /api/auth/jwt/create/` - Login
- `POST /api/auth/jwt/refresh/` - Refresh token
- `POST /api/auth/jwt/verify/` - Verify token
- `GET /api/auth/users/me/` - Get current user

### Classes
- `GET /api/attendance/classes/` - List classes
- `POST /api/attendance/classes/` - Create class
- `GET /api/attendance/classes/{id}/` - Get class details
- `PATCH /api/attendance/classes/{id}/` - Update class
- `DELETE /api/attendance/classes/{id}/` - Delete class
- `GET /api/attendance/classes/{id}/statistics/` - Get class statistics
- `POST /api/attendance/classes/{id}/bulk-upload-students/` - Bulk upload students

### Sessions
- `GET /api/attendance/sessions/?class_id={id}` - List sessions for a class
- `GET /api/attendance/sessions/{id}/` - Get session details
- `POST /api/attendance/sessions/` - Create new session
- `PATCH /api/attendance/sessions/{id}/` - Update session
- `DELETE /api/attendance/sessions/{id}/` - Delete session

### Students
- `GET /api/attendance/students/?class_id={id}` - List students for a class
- `GET /api/attendance/students/{id}/` - Get student details
- `POST /api/attendance/students/` - Create new student
- `PATCH /api/attendance/students/{id}/` - Update student
- `DELETE /api/attendance/students/{id}/` - Delete student

## 🎯 Future Development

The frontend is designed to be easily extensible. Planned features include:

- **Image Upload**: Upload session images for face detection
- **Attendance Reports**: View and export attendance data
- **Dashboard**: Overview of all classes and attendance statistics
- **User Profile**: Edit profile and change password
- **Dark/Light Theme Toggle**: Theme switching support
- **Export to CSV**: Download student and session data
- **Advanced Filtering**: Filter sessions by status, date range
- **Student Attendance History**: View individual student attendance
- **Email Notifications**: Notify students of session results

## 🏗️ Development Guidelines

### Code Style

- Use TypeScript for all new files
- Follow React hooks best practices
- Use functional components
- Keep components small and focused
- Use meaningful variable and function names

### State Management

- Use React Context for global state (auth, theme, etc.)
- Use local state (useState) for component-specific state
- Use useEffect for side effects and data fetching

### Styling

- Use TailwindCSS utility classes
- Follow the existing color scheme (dark theme)
- Keep custom CSS minimal
- Use the predefined CSS classes from `index.css`

### Adding New Pages

1. Create page component in `src/pages/`
2. Add route in `src/App.tsx`
3. Add API functions in `src/services/api.ts`
4. Add types in `src/types/index.ts`

### Adding New Components

1. Create component in `src/components/` or `src/components/ui/`
2. Use TypeScript interfaces for props
3. Export from index file if in `ui/` directory
4. Follow existing component patterns

## 🔧 Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## 🐛 Troubleshooting

### Port already in use
```bash
# Change port in vite.config.ts or use environment variable
PORT=3001 npm run dev
```

### API connection issues
- Ensure backend is running
- Check `VITE_API_BASE_URL` in `.env`
- Check browser console for CORS errors
- Verify backend CORS settings include frontend URL

### Build errors
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

## 📝 License

This project is part of the AttendanSee system. See the main project LICENSE file for details.

## 🤝 Contributing

This is a private project. For any questions or suggestions, please contact the development team.

---

**Built with ❤️ for AttendanSee**
