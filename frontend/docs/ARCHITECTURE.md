# AttendanSee Frontend - Architecture Overview

## System Architecture

The AttendanSee frontend is a modern single-page application (SPA) built with React and TypeScript, designed to provide a professional interface for managing classroom attendance through facial recognition.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                         Presentation Layer                   │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │  Login Page │  │ Classes Page│  │  Future Pages... │   │
│  └─────────────┘  └─────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                       Component Layer                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Layout  │  │ Protected│  │ UI Comps │  │  Modals  │   │
│  │          │  │  Route   │  │          │  │          │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                        State Layer                           │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  Auth Context    │         │  Local State     │         │
│  │  (Global State)  │         │  (Component)     │         │
│  └──────────────────┘         └──────────────────┘         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                       Service Layer                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              API Service (Axios)                      │  │
│  │  - Request/Response Interceptors                      │  │
│  │  - Token Management                                   │  │
│  │  - Automatic Token Refresh                            │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     Backend API Layer                        │
│                    (Django REST Framework)                   │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Patterns

### 1. Context Pattern (State Management)

**AuthContext** provides global authentication state:
- User information
- Authentication status
- Login/Logout functions
- Token management

Benefits:
- Centralized auth logic
- No prop drilling
- Easy to test
- Single source of truth

### 2. Protected Route Pattern

**ProtectedRoute** component wraps protected pages:
- Checks authentication status
- Redirects to login if not authenticated
- Shows loading state during auth check

### 3. API Service Pattern

Centralized API service with:
- Axios instance configuration
- Request interceptors (add auth token)
- Response interceptors (handle token refresh)
- Typed API functions
- Error handling

### 4. Component Composition

Reusable UI components:
- Small, focused components
- Clear prop interfaces
- Consistent styling
- Easy to maintain and test

## Data Flow

### Authentication Flow

```
User Login
    ↓
LoginPage → authAPI.login()
    ↓
Backend validates credentials
    ↓
Returns access + refresh tokens
    ↓
Tokens saved to localStorage
    ↓
AuthContext updates user state
    ↓
Redirect to /classes
```

### API Request Flow

```
Component triggers API call
    ↓
API service function called
    ↓
Request interceptor adds auth token
    ↓
HTTP request sent to backend
    ↓
Response received
    ↓
If 401 error:
    ├─→ Refresh token attempted
    ├─→ If successful: retry original request
    └─→ If failed: redirect to login
    ↓
Data returned to component
    ↓
Component state updated
    ↓
UI re-renders
```

### Class Management Flow

```
ClassesPage loads
    ↓
useEffect triggers fetchClasses()
    ↓
classesAPI.getClasses() called
    ↓
Data received and state updated
    ↓
Classes rendered in grid
    ↓
User clicks "Create Class"
    ↓
Modal opens with form
    ↓
User submits form
    ↓
classesAPI.createClass() called
    ↓
Success: modal closes, list refreshes
    ↓
Error: display error in modal
```

## Routing Structure

```
/
├── /login (public)
│   └── LoginPage
│
└── / (protected)
    ├── Layout (with header)
    │   ├── /classes
    │   │   └── ClassesPage
    │   │
    │   └── / (redirect to /classes)
    │
    └── * (404 redirect to /)
```

## Component Hierarchy

```
App
├── BrowserRouter
│   └── AuthProvider
│       └── Routes
│           ├── LoginPage (public)
│           │
│           └── ProtectedRoute
│               └── Layout
│                   ├── Header
│                   │   ├── Logo
│                   │   ├── User Info
│                   │   └── Logout Button
│                   │
│                   └── Outlet
│                       └── ClassesPage
│                           ├── Header Section
│                           │   ├── Title
│                           │   └── Create Button
│                           │
│                           ├── Class Cards Grid
│                           │   └── Card (multiple)
│                           │       ├── Class Info
│                           │       ├── Statistics
│                           │       └── Action Buttons
│                           │
│                           └── Modals
│                               ├── Create Modal
│                               ├── Edit Modal
│                               └── Delete Modal
```

## State Management Strategy

### Global State (Context)
- Authentication state
- Current user information
- Theme (future)

### Local State (useState)
- Form inputs
- Modal visibility
- Loading states
- Error messages
- List data (classes)

### Server State
- Fetched from API
- Cached in component state
- Refetched on mutations

## Error Handling Strategy

### Levels of Error Handling

1. **API Service Level**
   - Request/response interceptors
   - Token refresh logic
   - Network error handling

2. **Component Level**
   - Try/catch blocks
   - Error state management
   - User-friendly error messages

3. **UI Level**
   - Error message display
   - Form validation errors
   - Global error boundaries (future)

### Error Display

- **Form Errors**: Inline below inputs
- **API Errors**: Modal or page-level alerts
- **Auth Errors**: Redirect to login
- **Network Errors**: Retry prompts

## Performance Optimizations

### Current Optimizations

1. **Code Splitting**
   - React lazy loading (ready for future pages)
   - Route-based splitting

2. **Build Optimization**
   - Vite for fast builds
   - Tree shaking
   - Minification

3. **Asset Optimization**
   - Gzip compression (nginx)
   - Static asset caching
   - SVG icons (lightweight)

### Future Optimizations

- React Query for server state
- Virtual scrolling for large lists
- Image lazy loading
- Service worker for offline support

## Security Considerations

### Implemented

1. **Authentication**
   - JWT tokens with refresh mechanism
   - Token stored in localStorage
   - Automatic token refresh
   - Redirect on auth failure

2. **API Security**
   - CORS validation
   - Auth token in headers
   - HTTPS in production

3. **XSS Prevention**
   - React's built-in XSS protection
   - No dangerouslySetInnerHTML usage
   - Input sanitization

4. **CSRF Protection**
   - Token-based auth (no cookies)
   - Backend CSRF middleware

### Future Enhancements

- HTTP-only cookies for tokens
- Content Security Policy
- Rate limiting on frontend
- Session timeout warnings

## Deployment Architecture

### Development
```
Vite Dev Server (localhost:3000)
    ↓
Hot Module Replacement
    ↓
Development Backend (localhost:8000)
```

### Production (Docker)
```
Docker Container
    ├── Build Stage (Node.js)
    │   ├── Install dependencies
    │   ├── Build React app
    │   └── Optimize assets
    │
    └── Runtime Stage (Nginx)
        ├── Serve static files
        ├── Handle routing (SPA)
        ├── Gzip compression
        └── Security headers
```

## Scalability Considerations

### Current Design Supports

1. **Feature Addition**
   - Modular component structure
   - Separation of concerns
   - Easy to add new pages/routes

2. **API Changes**
   - Centralized API service
   - Type definitions
   - Easy to update endpoints

3. **UI Changes**
   - TailwindCSS utility classes
   - Reusable components
   - Consistent design system

### Future Scalability

- State management library (Redux/Zustand)
- Micro-frontend architecture
- Component library extraction
- Multi-tenancy support

## Testing Strategy (Future)

### Unit Testing
- Component testing (React Testing Library)
- Utility function testing (Jest)
- API service testing (Mock axios)

### Integration Testing
- User flow testing
- API integration testing
- Auth flow testing

### E2E Testing
- Cypress or Playwright
- Critical user journeys
- Cross-browser testing

## Development Workflow

```
1. Feature Planning
   ↓
2. Create Types (if needed)
   ↓
3. Create API Functions
   ↓
4. Create Components
   ↓
5. Add Routes
   ↓
6. Test Manually
   ↓
7. Code Review
   ↓
8. Deploy
```

## Technology Choices Rationale

| Technology | Reason |
|------------|--------|
| React | Industry standard, great ecosystem, component-based |
| TypeScript | Type safety, better DX, catches errors early |
| Vite | Fast builds, great DX, modern tooling |
| TailwindCSS | Rapid development, consistent design, small bundle |
| Axios | Interceptors, better error handling than fetch |
| React Router | De facto routing solution, excellent docs |
| Lucide React | Modern icons, tree-shakeable, consistent style |

## Best Practices Applied

1. **TypeScript First**: All code is typed
2. **Component Reusability**: DRY principle
3. **Separation of Concerns**: Clear layer boundaries
4. **Error Handling**: Comprehensive error management
5. **Security**: Auth and XSS protection
6. **Performance**: Optimized builds and caching
7. **Documentation**: Well-documented code
8. **Consistency**: Uniform code style
9. **Accessibility**: Semantic HTML (room for improvement)
10. **Maintainability**: Clean, readable code

## Future Architecture Improvements

1. **State Management**
   - Implement React Query for server state
   - Consider Zustand for complex client state

2. **Testing**
   - Add comprehensive test suite
   - CI/CD integration

3. **Accessibility**
   - ARIA labels
   - Keyboard navigation
   - Screen reader support

4. **Performance**
   - Implement virtual scrolling
   - Add service worker
   - Image optimization

5. **Monitoring**
   - Error tracking (Sentry)
   - Analytics
   - Performance monitoring

---

This architecture is designed to be maintainable, scalable, and easy to understand for future developers.
