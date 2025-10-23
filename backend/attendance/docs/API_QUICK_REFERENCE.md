# API Quick Reference

## Endpoints Summary

| Resource | Endpoint | Methods | Description |
|----------|----------|---------|-------------|
| **Classes** | `/api/attendance/classes/` | GET, POST | List/Create classes |
| | `/api/attendance/classes/{id}/` | GET, PUT, PATCH, DELETE | Class CRUD |
| | `/api/attendance/classes/{id}/students/` | GET | List class students |
| | `/api/attendance/classes/{id}/sessions/` | GET | List class sessions |
| | `/api/attendance/classes/{id}/statistics/` | GET | Class statistics |
| **Students** | `/api/attendance/students/` | GET, POST | List/Create students |
| | `/api/attendance/students/{id}/` | GET, PUT, PATCH, DELETE | Student CRUD |
| | `/api/attendance/students/{id}/attendance/` | GET | Student attendance stats |
| **Sessions** | `/api/attendance/sessions/` | GET, POST | List/Create sessions |
| | `/api/attendance/sessions/{id}/` | GET, PUT, PATCH, DELETE | Session CRUD |
| | `/api/attendance/sessions/{id}/images/` | GET | List session images |
| | `/api/attendance/sessions/{id}/attendance/` | GET | Session attendance report |
| **Images** | `/api/attendance/images/` | GET, POST | List/Upload images |
| | `/api/attendance/images/{id}/` | GET, DELETE | Image Read/Delete |
| | `/api/attendance/images/{id}/face_crops/` | GET | List image face crops |
| | `/api/attendance/images/{id}/mark_processed/` | POST | Mark as processed |
| **Face Crops** | `/api/attendance/face-crops/` | GET | List face crops |
| | `/api/attendance/face-crops/{id}/` | GET, PATCH | Crop Read/Update student |
| | `/api/attendance/face-crops/{id}/unidentify/` | POST | Clear student assignment |

## Permissions

### Admin (is_staff=True)
✅ Full access to ALL resources

### Regular User
- ✅ **Class**: Full CRUD on own classes
- ✅ **Student**: Full CRUD in own classes
- ✅ **Session**: Full CRUD in own classes  
- ✅ **Image**: Create, Read, Delete in own sessions
- ✅ **Face Crop**: Read, Update student field in own classes
- ❌ Cannot access other users' resources

## Updatable Fields

| Model | Fields You Can Update |
|-------|----------------------|
| **Class** | `name`, `description`, `is_active` |
| **Student** | `first_name`, `last_name`, `student_id`, `email` |
| **Session** | `name`, `date`, `start_time`, `end_time`, `notes` |
| **Image** | None (Create/Delete only) |
| **Face Crop** | `student` (only this field) |

## Query Parameters

### Students
- `?class_id=1` - Filter by class

### Sessions
- `?class_id=1` - Filter by class

### Images
- `?session_id=1` - Filter by session
- `?is_processed=true` - Filter by processing status

### Face Crops
- `?image_id=1` - Filter by image
- `?session_id=1` - Filter by session
- `?is_identified=true` - Filter by identification status
- `?student_id=1` - Filter by student

## Quick Commands

### Run Tests
```bash
# All attendance API tests
pytest attendance/tests/test_api.py -v

# Specific test class
pytest attendance/tests/test_api.py::TestClassAPI -v

# With coverage
pytest attendance/tests/test_api.py --cov=attendance.views --cov=attendance.serializers
```

### Test Endpoint
```bash
# Login
curl -X POST http://localhost:8000/api/auth/jwt/create/ \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"pass"}'

# Use token
curl -X GET http://localhost:8000/api/attendance/classes/ \
  -H "Authorization: Bearer <token>"
```

### Common Responses

#### Success
- `200 OK` - Success (GET, PUT, PATCH)
- `201 Created` - Created (POST)
- `204 No Content` - Deleted (DELETE)

#### Errors
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - No permission
- `404 Not Found` - Not found or no access

## Example Requests

### Create Class
```json
POST /api/attendance/classes/
{
  "name": "CS 101",
  "description": "Intro to CS",
  "is_active": true
}
```

### Create Student
```json
POST /api/attendance/students/
{
  "class_enrolled": 1,
  "first_name": "Alice",
  "last_name": "Smith",
  "student_id": "S001",
  "email": "alice@example.com"
}
```

### Create Session
```json
POST /api/attendance/sessions/
{
  "class_session": 1,
  "name": "Week 1",
  "date": "2025-10-23",
  "start_time": "10:00:00",
  "end_time": "11:30:00",
  "notes": "First lecture"
}
```

### Upload Image
```json
POST /api/attendance/images/
{
  "session": 1,
  "original_image_path": "/uploads/img1.jpg"
}
```

### Mark Image Processed
```json
POST /api/attendance/images/1/mark_processed/
{
  "processed_image_path": "/processed/img1.jpg"
}
```

### Assign Student to Face Crop
```json
PATCH /api/attendance/face-crops/1/
{
  "student": 5
}
```

### Unidentify Face Crop
```json
POST /api/attendance/face-crops/1/unidentify/
```

## Testing in Python

```python
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

# Setup
client = APIClient()
user = User.objects.create_user(username='test', password='test123')
client.force_authenticate(user=user)

# Create class
response = client.post('/api/attendance/classes/', {
    'name': 'Test Class'
})
assert response.status_code == 201

# List classes
response = client.get('/api/attendance/classes/')
assert response.status_code == 200
```

## Tips

1. **Always authenticate** - All endpoints require authentication
2. **Check permissions** - Users can only access their own resources
3. **Use PATCH** - For partial updates instead of PUT
4. **Filter lists** - Use query params to reduce response size
5. **Use nested endpoints** - For related data (e.g., `/classes/{id}/students/`)
6. **Check validation** - Serializer validation prevents invalid data
7. **Admin access** - Admins bypass ownership checks
