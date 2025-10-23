# Attendance API Documentation

## Base URL
```
/api/attendance/
```

## Authentication
All endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Permissions
- **Admin Users**: Full CRUD access to all resources
- **Regular Users**: CRUD access to their own resources only

---

## Endpoints

### Classes

#### List Classes
```http
GET /api/attendance/classes/
```
Returns all classes owned by the authenticated user (or all classes for admin).

**Response:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "owner": "professor",
      "owner_id": 1,
      "name": "Computer Science 101",
      "description": "Introduction to CS",
      "is_active": true,
      "created_at": "2025-10-23T10:00:00Z",
      "updated_at": "2025-10-23T10:00:00Z",
      "student_count": 25,
      "session_count": 10
    }
  ]
}
```

#### Create Class
```http
POST /api/attendance/classes/
Content-Type: application/json

{
  "name": "Physics 101",
  "description": "Introduction to Physics",
  "is_active": true
}
```

#### Retrieve Class
```http
GET /api/attendance/classes/{id}/
```

#### Update Class
```http
PUT /api/attendance/classes/{id}/
PATCH /api/attendance/classes/{id}/

{
  "name": "Physics 102",
  "description": "Updated description",
  "is_active": false
}
```

#### Delete Class
```http
DELETE /api/attendance/classes/{id}/
```

#### Get Class Students
```http
GET /api/attendance/classes/{id}/students/
```

#### Get Class Sessions
```http
GET /api/attendance/classes/{id}/sessions/
```

#### Get Class Statistics
```http
GET /api/attendance/classes/{id}/statistics/
```

**Response:**
```json
{
  "student_count": 25,
  "session_count": 10,
  "total_images": 30,
  "processed_images": 28,
  "total_face_crops": 150,
  "identified_faces": 140
}
```

---

### Students

#### List Students
```http
GET /api/attendance/students/
```

**Query Parameters:**
- `class_id`: Filter by class ID

#### Create Student
```http
POST /api/attendance/students/
Content-Type: application/json

{
  "class_enrolled": 1,
  "first_name": "Alice",
  "last_name": "Smith",
  "student_id": "S001",
  "email": "alice@example.com"
}
```

#### Retrieve Student
```http
GET /api/attendance/students/{id}/
```

#### Update Student
```http
PUT /api/attendance/students/{id}/
PATCH /api/attendance/students/{id}/

{
  "first_name": "Alice",
  "last_name": "Johnson",
  "student_id": "S001",
  "email": "alice.j@example.com"
}
```

#### Delete Student
```http
DELETE /api/attendance/students/{id}/
```

#### Get Student Attendance
```http
GET /api/attendance/students/{id}/attendance/
```

**Response:**
```json
{
  "total_sessions": 10,
  "attended_sessions": 8,
  "attendance_rate": 80.0,
  "total_detections": 12
}
```

---

### Sessions

#### List Sessions
```http
GET /api/attendance/sessions/
```

**Query Parameters:**
- `class_id`: Filter by class ID

#### Create Session
```http
POST /api/attendance/sessions/
Content-Type: application/json

{
  "class_session": 1,
  "name": "Week 1 - Introduction",
  "date": "2025-10-23",
  "start_time": "10:00:00",
  "end_time": "11:30:00",
  "notes": "First lecture"
}
```

#### Retrieve Session
```http
GET /api/attendance/sessions/{id}/
```

#### Update Session
```http
PUT /api/attendance/sessions/{id}/
PATCH /api/attendance/sessions/{id}/

{
  "name": "Week 1 - Introduction (Updated)",
  "date": "2025-10-23",
  "notes": "Updated notes"
}
```

#### Delete Session
```http
DELETE /api/attendance/sessions/{id}/
```

#### Get Session Images
```http
GET /api/attendance/sessions/{id}/images/
```

#### Get Session Attendance
```http
GET /api/attendance/sessions/{id}/attendance/
```

**Response:**
```json
{
  "session": { ... },
  "total_students": 25,
  "present_count": 23,
  "absent_count": 2,
  "attendance": [
    {
      "id": 1,
      "name": "Alice Smith",
      "student_id": "S001",
      "present": true,
      "detection_count": 2
    },
    {
      "id": 2,
      "name": "Bob Jones",
      "student_id": "S002",
      "present": false,
      "detection_count": 0
    }
  ]
}
```

---

### Images

#### List Images
```http
GET /api/attendance/images/
```

**Query Parameters:**
- `session_id`: Filter by session ID
- `is_processed`: Filter by processing status (true/false)

#### Create Image
```http
POST /api/attendance/images/
Content-Type: application/json

{
  "session": 1,
  "original_image_path": "/uploads/session1_img1.jpg"
}
```

#### Retrieve Image
```http
GET /api/attendance/images/{id}/
```

#### Delete Image
```http
DELETE /api/attendance/images/{id}/
```

#### Get Image Face Crops
```http
GET /api/attendance/images/{id}/face_crops/
```

#### Mark Image as Processed
```http
POST /api/attendance/images/{id}/mark_processed/
Content-Type: application/json

{
  "processed_image_path": "/processed/session1_img1.jpg"
}
```

---

### Face Crops

#### List Face Crops
```http
GET /api/attendance/face-crops/
```

**Query Parameters:**
- `image_id`: Filter by image ID
- `session_id`: Filter by session ID
- `is_identified`: Filter by identification status (true/false)
- `student_id`: Filter by student ID

#### Retrieve Face Crop
```http
GET /api/attendance/face-crops/{id}/
```

**Response (Detailed):**
```json
{
  "id": 1,
  "image": 1,
  "image_id": 1,
  "student": 5,
  "student_name": "Alice Smith",
  "crop_image_path": "/crops/crop1.jpg",
  "coordinates": "100,150,200,250",
  "coordinates_dict": {
    "x": 100,
    "y": 150,
    "width": 200,
    "height": 250
  },
  "confidence_score": 0.95,
  "is_identified": true,
  "created_at": "2025-10-23T10:00:00Z",
  "updated_at": "2025-10-23T10:05:00Z",
  "session_id": 1,
  "session_name": "Week 1",
  "class_id": 1,
  "class_name": "CS 101"
}
```

#### Update Face Crop (Assign Student)
```http
PATCH /api/attendance/face-crops/{id}/
Content-Type: application/json

{
  "student": 5
}
```

**Note:** Only the `student` field can be updated. Setting `student` to a value automatically sets `is_identified` to `true`. Setting `student` to `null` clears the identification.

#### Unidentify Face Crop
```http
POST /api/attendance/face-crops/{id}/unidentify/
```

Clears the student assignment and sets `is_identified` to `false`.

---

## Error Responses

### 400 Bad Request
```json
{
  "field_name": ["Error message"]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

---

## Common Validation Errors

### Creating Student in Another User's Class
```json
{
  "class_enrolled": ["You can only add students to your own classes."]
}
```

### Assigning Student from Different Class to Face Crop
```json
{
  "student": ["Student must belong to the same class as the session."]
}
```

---

## Workflow Example

### 1. Create a Class
```http
POST /api/attendance/classes/
{
  "name": "CS 101",
  "description": "Intro to CS"
}
```

### 2. Add Students
```http
POST /api/attendance/students/
{
  "class_enrolled": 1,
  "first_name": "Alice",
  "last_name": "Smith"
}
```

### 3. Create a Session
```http
POST /api/attendance/sessions/
{
  "class_session": 1,
  "name": "Week 1",
  "date": "2025-10-23"
}
```

### 4. Upload Image
```http
POST /api/attendance/images/
{
  "session": 1,
  "original_image_path": "/uploads/img1.jpg"
}
```

### 5. Mark Image as Processed (after face detection)
```http
POST /api/attendance/images/1/mark_processed/
{
  "processed_image_path": "/processed/img1.jpg"
}
```

### 6. Assign Student to Face Crop
```http
PATCH /api/attendance/face-crops/1/
{
  "student": 1
}
```

### 7. Get Session Attendance
```http
GET /api/attendance/sessions/1/attendance/
```

---

## Filtering and Pagination

All list endpoints support pagination. Use the `page` query parameter:
```http
GET /api/attendance/classes/?page=2
```

Default page size is 20 items. This can be configured in settings.

---

## Tips

1. **Always check ownership**: Users can only access their own resources unless they're admin.

2. **Use filters**: Utilize query parameters to filter results (e.g., `?class_id=1`).

3. **Partial updates**: Use `PATCH` for updating individual fields instead of `PUT` which requires all fields.

4. **Related data**: Use nested endpoints like `/classes/{id}/students/` to get related data.

5. **Statistics**: Use the `/statistics/` and `/attendance/` endpoints for analytics.
