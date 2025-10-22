# Attendance App Database Schema

## Entity Relationship Diagram (ERD)

```
┌─────────────────────┐
│       User          │
│  (from auth app)    │
│─────────────────────│
│ - id (PK)           │
│ - username          │
│ - email             │
│ - password          │
│ - is_staff          │
└──────────┬──────────┘
           │
           │ 1:N (owner)
           │ CASCADE DELETE
           ▼
┌─────────────────────┐
│       Class         │
│─────────────────────│
│ - id (PK)           │
│ - owner (FK) ───────┼──► User
│ - name              │
│ - description       │
│ - is_active         │
│ - created_at        │
│ - updated_at        │
└──────┬──────┬───────┘
       │      │
       │      │ 1:N (class_session)
       │      │ CASCADE DELETE
       │      │
       │      ▼
       │   ┌─────────────────────┐
       │   │      Session        │
       │   │─────────────────────│
       │   │ - id (PK)           │
       │   │ - class_session(FK) │
       │   │ - name              │
       │   │ - date              │
       │   │ - start_time        │
       │   │ - end_time          │
       │   │ - notes             │
       │   │ - is_processed      │
       │   │ - created_at        │
       │   │ - updated_at        │
       │   └──────────┬──────────┘
       │              │
       │              │ 1:N (session)
       │              │ CASCADE DELETE
       │              │
       │              ▼
       │           ┌─────────────────────┐
       │           │       Image         │
       │           │─────────────────────│
       │           │ - id (PK)           │
       │           │ - session (FK)      │
       │           │ - original_path     │
       │           │ - processed_path    │
       │           │ - upload_date       │
       │           │ - is_processed      │
       │           │ - processing_date   │
       │           │ - created_at        │
       │           │ - updated_at        │
       │           └──────────┬──────────┘
       │                      │
       │                      │ 1:N (image)
       │                      │ CASCADE DELETE
       │                      │
       │ 1:N (class_enrolled) │
       │ CASCADE DELETE       │
       │                      │
       ▼                      ▼
┌─────────────────────┐   ┌─────────────────────┐
│      Student        │   │     FaceCrop        │
│─────────────────────│   │─────────────────────│
│ - id (PK)           │   │ - id (PK)           │
│ - class_enrolled(FK)│◄──┼─ student (FK)       │  N:1 (student)
│ - first_name        │   │ - image (FK)        │  SET_NULL on delete
│ - last_name         │   │ - crop_path         │
│ - student_id        │   │ - coordinates       │
│ - email             │   │ - confidence_score  │
│ - created_at        │   │ - is_identified     │
└─────────────────────┘   │ - created_at        │
                          │ - updated_at        │
                          └─────────────────────┘

UNIQUE: (first_name, last_name, class_enrolled)
```

## Cascade Behaviors

### DELETE Cascades
```
User DELETE
  ├── Class DELETE
  │   ├── Student DELETE
  │   │   └── FaceCrop.student = NULL (SET_NULL)
  │   └── Session DELETE
  │       └── Image DELETE
  │           └── FaceCrop DELETE
```

### Example Scenarios

#### Scenario 1: User (Professor) Deleted
```
DELETE User(id=1)
  → DELETE Class(owner=1)
    → DELETE Student(class_enrolled=Class.id)
      → SET NULL FaceCrop(student=Student.id)
    → DELETE Session(class_session=Class.id)
      → DELETE Image(session=Session.id)
        → DELETE FaceCrop(image=Image.id)
```

#### Scenario 2: Student Deleted
```
DELETE Student(id=5)
  → UPDATE FaceCrop SET student=NULL WHERE student=5
  (Face crops preserved for historical data)
```

## Data Flow

### 1. Setup Phase
```
Professor → Create Class → Add Students
```

### 2. Session Creation
```
Professor → Create Session for Class
```

### 3. Image Upload & Processing
```
Professor → Upload Images → Core Logic Processes → Save Results
  1. Upload: Store original_image_path
  2. Process: Core detects faces
  3. Save: Store processed_image_path
  4. Detect: Create FaceCrop for each face
  5. Mark: image.mark_as_processed()
```

### 4. Face Identification
```
Core Logic → Identify Faces → Link to Students
  1. Match: Core matches face to student
  2. Link: crop.identify_student(student, confidence)
  3. Track: Attendance automatically tracked
```

### 5. Status Updates
```
Image processed → Session.update_processing_status()
  IF all images processed:
    Session.is_processed = True
```

## Key Relationships

| Relationship | Type | On Delete | Description |
|--------------|------|-----------|-------------|
| User → Class | 1:N | CASCADE | Professor owns classes |
| Class → Student | 1:N | CASCADE | Students enrolled in class |
| Class → Session | 1:N | CASCADE | Sessions belong to class |
| Session → Image | 1:N | CASCADE | Images taken in session |
| Image → FaceCrop | 1:N | CASCADE | Faces detected in image |
| Student → FaceCrop | 1:N | SET_NULL | Face crops of student |

## Indexes

Strategic indexes for performance:

```sql
-- Class indexes
CREATE INDEX idx_class_owner_created ON classes(owner_id, created_at DESC);
CREATE INDEX idx_class_active ON classes(is_active);

-- Student indexes
CREATE INDEX idx_student_class_name ON students(class_enrolled_id, last_name, first_name);

-- Session indexes
CREATE INDEX idx_session_class_date ON sessions(class_session_id, date DESC);
CREATE INDEX idx_session_processed ON sessions(is_processed);

-- Image indexes
CREATE INDEX idx_image_session_upload ON images(session_id, upload_date DESC);
CREATE INDEX idx_image_processed ON images(is_processed);

-- FaceCrop indexes
CREATE INDEX idx_crop_image_created ON face_crops(image_id, created_at DESC);
CREATE INDEX idx_crop_student ON face_crops(student_id);
CREATE INDEX idx_crop_identified ON face_crops(is_identified);
```

## Common Queries

### Get all students in a class
```python
students = Student.objects.filter(class_enrolled=class_id)
```

### Get sessions for a class
```python
sessions = Session.objects.filter(class_session=class_id).order_by('-date')
```

### Get images in a session
```python
images = Image.objects.filter(session=session_id)
```

### Get face crops in an image
```python
crops = FaceCrop.objects.filter(image=image_id)
```

### Get identified vs unidentified faces
```python
identified = FaceCrop.objects.filter(image=image_id, is_identified=True)
unidentified = FaceCrop.objects.filter(image=image_id, is_identified=False)
```

### Get attendance for a student
```python
sessions_attended = Session.objects.filter(
    images__face_crops__student=student_id
).distinct()
```

### Get present students in a session
```python
present = Student.objects.filter(
    face_crops__image__session=session_id
).distinct()
```

### Get attendance rate
```python
from django.db.models import Count

classes_with_stats = Class.objects.annotate(
    total_sessions=Count('sessions', distinct=True),
    total_students=Count('students', distinct=True)
)
```
