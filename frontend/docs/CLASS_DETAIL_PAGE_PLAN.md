# Class Detail Page - Design & Implementation Plan

## 📋 Overview

The Class Detail page will be a comprehensive dashboard for managing a specific class, including sessions and students. It will replace navigating away from the classes page and provide a dedicated workspace for class management.

## 🎯 Requirements

### Core Features
1. **Class Information Display**
   - Class name, description, status
   - Edit and delete actions
   - Statistics display

2. **Session Management**
   - List all sessions (up to 50+)
   - Create new session
   - Edit session details
   - Delete session
   - Session statistics (images, attendance)

3. **Student Management**
   - List all students
   - Add individual student
   - Bulk upload via CSV (with header detection)
   - Edit student information
   - Delete student

## 🎨 Design Strategy

### Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│ Header (Breadcrumb + Actions)                               │
│ Home > Classes > [Class Name]              [Edit] [Delete]  │
├─────────────────────────────────────────────────────────────┤
│ Class Info Card                                             │
│ Name, Description, Status, Statistics                       │
├─────────────────────────────────────────────────────────────┤
│ Tab Navigation                                              │
│ [Sessions] [Students]                                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Tab Content Area                                            │
│                                                             │
│ Sessions Tab:                                               │
│ ┌───────────────────────────────────┐                      │
│ │ [Create Session]        [Search]  │                      │
│ ├───────────────────────────────────┤                      │
│ │ Session List (Compact Table)      │                      │
│ │ - Date | Name | Status | Actions  │                      │
│ │ - Pagination (10 per page)        │                      │
│ └───────────────────────────────────┘                      │
│                                                             │
│ Students Tab:                                               │
│ ┌───────────────────────────────────┐                      │
│ │ [Add Student] [Upload CSV] [...]  │                      │
│ ├───────────────────────────────────┤                      │
│ │ Student List (Compact Cards/Table)│                      │
│ │ - Name | Student ID | Actions     │                      │
│ │ - Search functionality            │                      │
│ └───────────────────────────────────┘                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Component Breakdown

1. **ClassDetailPage** (Main container)
   - Header with breadcrumb navigation
   - Class information section
   - Tab navigation (Sessions/Students)
   - Tab content rendering

2. **ClassInfoSection**
   - Display class details
   - Statistics cards
   - Edit/Delete actions

3. **SessionsTab**
   - Session list (table format for compactness)
   - Create session button
   - Session modals (Create/Edit/Delete)
   - Pagination for 50+ sessions
   - Search/filter functionality

4. **StudentsTab**
   - Student list (cards or table)
   - Add student button
   - Upload CSV button
   - Student modals (Add/Edit/Delete/BulkUpload)
   - Search functionality

### Design Decisions

#### For Sessions (Handling 50+ items)
- **Table view** instead of cards (more compact)
- **Pagination**: 10-15 sessions per page
- **Sorting**: By date (newest first)
- **Search**: By name or date
- **Columns**: Date | Name | Images | Attendance | Status | Actions
- **Actions**: Inline icons (Edit, Delete)

#### For Students
- **Flexible view**: Can use cards or table
- **Search**: Real-time filtering by name or student ID
- **Bulk upload**: Modal with file picker and header checkbox
- **Columns/Info**: Name | Student ID | Email | Actions

## 🔌 API Integration

### Endpoints to Use

#### Class
- `GET /api/attendance/classes/{id}/` - Get class details
- `PATCH /api/attendance/classes/{id}/` - Update class
- `DELETE /api/attendance/classes/{id}/` - Delete class
- `GET /api/attendance/classes/{id}/statistics/` - Get statistics
- `GET /api/attendance/classes/{id}/sessions/` - Get sessions
- `GET /api/attendance/classes/{id}/students/` - Get students

#### Sessions
- `GET /api/attendance/sessions/?class_id={id}` - List sessions
- `POST /api/attendance/sessions/` - Create session
- `PATCH /api/attendance/sessions/{id}/` - Update session
- `DELETE /api/attendance/sessions/{id}/` - Delete session

#### Students
- `GET /api/attendance/students/?class_id={id}` - List students
- `POST /api/attendance/students/` - Create student
- `PATCH /api/attendance/students/{id}/` - Update student
- `DELETE /api/attendance/students/{id}/` - Delete student
- `POST /api/attendance/classes/{id}/bulk-upload-students/` - Bulk upload

## 🎨 UI Components Needed

### New Components
1. **Tabs** - Tab navigation component
2. **Table** - Data table component
3. **Pagination** - Pagination controls
4. **Breadcrumb** - Navigation breadcrumb
5. **FileUpload** - File upload component
6. **SearchInput** - Search input with icon
7. **StatCard** - Statistics card component
8. **Badge** - Status badge component

### Existing Components to Use
- Button, Input, Modal, Card, LoadingSpinner

## 📱 User Flows

### Navigate to Class Detail
```
Classes Page → Click on Class Card → Class Detail Page
```

### Manage Sessions
```
Class Detail → Sessions Tab → Create Session → Modal → Submit → Refresh List
Class Detail → Sessions Tab → Edit Session → Modal → Submit → Refresh List
Class Detail → Sessions Tab → Delete Session → Confirmation → Delete → Refresh
```

### Manage Students
```
Class Detail → Students Tab → Add Student → Modal → Submit → Refresh List
Class Detail → Students Tab → Upload CSV → Modal → Select File → Configure → Submit
Class Detail → Students Tab → Edit Student → Modal → Submit → Refresh List
Class Detail → Students Tab → Delete Student → Confirmation → Delete → Refresh
```

## 🎯 Implementation Steps

### Phase 1: Setup & Routing
1. Create types for Session and Student (extend existing)
2. Add API functions for sessions and students
3. Create route for class detail page
4. Add navigation from classes page

### Phase 2: Core Components
1. Create Tabs component
2. Create Table component
3. Create Pagination component
4. Create Breadcrumb component
5. Create StatCard component
6. Create Badge component

### Phase 3: Class Detail Page Structure
1. Create ClassDetailPage component
2. Implement header with breadcrumb
3. Implement class info section
4. Implement tab navigation
5. Setup routing between tabs

### Phase 4: Sessions Management
1. Create SessionsTab component
2. Implement session list table
3. Create session modals (Create/Edit/Delete)
4. Implement pagination
5. Add search functionality

### Phase 5: Students Management
1. Create StudentsTab component
2. Implement student list
3. Create student modals (Add/Edit/Delete)
4. Implement CSV upload modal
5. Add search functionality

### Phase 6: Polish
1. Add loading states
2. Add error handling
3. Add empty states
4. Add animations
5. Test responsive design

## 💾 State Management

### Local State
- Current class data
- Current tab (sessions/students)
- Sessions list
- Students list
- Pagination state (current page, total pages)
- Search queries
- Modal states (open/close, selected item)
- Loading states
- Error states

### API Data Flow
```
Component Mount
  ↓
Fetch Class Details
  ↓
Fetch Statistics
  ↓
Fetch Sessions/Students (based on active tab)
  ↓
Display Data
```

## 🎨 Design Consistency

- Use existing color scheme (dark theme)
- Match ClassesPage design patterns
- Reuse existing UI components
- Maintain consistent spacing and typography
- Use same modal patterns
- Consistent button styles and actions

## 📊 Data Display

### Session Table Columns
| Date | Name | Images | Faces | Status | Actions |
|------|------|--------|-------|--------|---------|
| 2024-10-23 | Lecture 1 | 5 | 23/25 | ✓ | [Edit][Delete] |

### Student List View
- Card view for small lists (< 20)
- Table view for large lists (> 20)
- Switch between views option

## 🔍 Search & Filter

### Sessions
- Search by: Name, Date
- Filter by: Processed status
- Sort by: Date (desc/asc)

### Students
- Search by: Name, Student ID, Email
- Sort by: Name, Student ID

## ✅ Success Criteria

- [ ] User can navigate to class detail from classes page
- [ ] User can view class information and statistics
- [ ] User can edit/delete class from detail page
- [ ] User can view all sessions (paginated)
- [ ] User can create/edit/delete sessions
- [ ] User can search sessions
- [ ] User can view all students
- [ ] User can add individual student
- [ ] User can upload CSV with students (with header option)
- [ ] User can edit/delete students
- [ ] User can search students
- [ ] All actions have loading states
- [ ] All actions have error handling
- [ ] Design is consistent with existing pages
- [ ] Page is responsive

## 🎯 Future Enhancements

- Export students to CSV
- Filter sessions by date range
- Bulk student operations (delete multiple)
- Session detail view (images, attendance details)
- Student attendance history
- Quick stats on hover
- Keyboard shortcuts

---

This plan provides a comprehensive roadmap for implementing a professional, scalable class detail page that handles the requirements while maintaining design consistency.
