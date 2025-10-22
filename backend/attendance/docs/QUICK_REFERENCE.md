# Attendance Models - Quick Reference

## Model Hierarchy
```
User (auth) → Class → Student
                   → Session → Image → FaceCrop
```

## Quick Model Access

### Class
```python
from attendance.models import Class

# Create
cs_class = Class.objects.create(owner=user, name='CS 101', description='Intro to CS')

# Query
my_classes = Class.objects.filter(owner=user, is_active=True)
active_classes = Class.objects.filter(is_active=True)

# Relationships
cs_class.students.all()  # All students
cs_class.sessions.all()  # All sessions
```

### Student
```python
from attendance.models import Student

# Create
alice = Student.objects.create(
    class_enrolled=cs_class,
    first_name='Alice',
    last_name='Smith',
    student_id='CS001',
    email='alice@example.com'
)

# Query
students = Student.objects.filter(class_enrolled=cs_class).order_by('last_name')
alice = Student.objects.get(class_enrolled=cs_class, first_name='Alice', last_name='Smith')

# Properties
alice.full_name  # "Alice Smith"

# Relationships
alice.face_crops.all()  # All face detections
```

### Session
```python
from attendance.models import Session
from datetime import date, time

# Create
session = Session.objects.create(
    class_session=cs_class,
    name='Week 1 - Introduction',
    date=date(2025, 10, 22),
    start_time=time(10, 0),
    end_time=time(11, 30),
    notes='First lecture'
)

# Query
recent_sessions = Session.objects.filter(class_session=cs_class).order_by('-date')[:5]

# Methods
session.update_processing_status()  # Update based on image processing

# Relationships
session.images.all()  # All images in this session
```

### Image
```python
from attendance.models import Image

# Create
image = Image.objects.create(
    session=session,
    original_image_path='/uploads/2025/10/22/image1.jpg'
)

# Query
unprocessed = Image.objects.filter(session=session, is_processed=False)
processed = Image.objects.filter(session=session, is_processed=True)

# Methods
image.mark_as_processed('/processed/2025/10/22/image1_proc.jpg')

# Relationships
image.face_crops.all()  # All face detections
```

### FaceCrop
```python
from attendance.models import FaceCrop

# Create
crop = FaceCrop.objects.create(
    image=image,
    crop_image_path='/crops/2025/10/22/face1.jpg',
    coordinates=FaceCrop.format_coordinates(100, 150, 200, 250)
)

# Query
identified = FaceCrop.objects.filter(image=image, is_identified=True)
unidentified = FaceCrop.objects.filter(image=image, is_identified=False)
student_crops = FaceCrop.objects.filter(student=alice)

# Methods
crop.identify_student(alice, confidence=0.95)
coords = crop.parse_coordinates()  # {'x': 100, 'y': 150, 'width': 200, 'height': 250}
coords_str = FaceCrop.format_coordinates(100, 150, 200, 250)  # "100,150,200,250"

# Relationships
crop.image  # Parent image
crop.student  # Identified student (or None)
```

## Common Workflows

### Complete Attendance Workflow
```python
from django.contrib.auth import get_user_model
from attendance.models import *
from datetime import date

User = get_user_model()

# 1. Setup
professor = User.objects.get(username='prof')
cs_class = Class.objects.create(owner=professor, name='CS 101')
alice = Student.objects.create(class_enrolled=cs_class, first_name='Alice', last_name='Smith')
bob = Student.objects.create(class_enrolled=cs_class, first_name='Bob', last_name='Jones')

# 2. Create Session
session = Session.objects.create(
    class_session=cs_class,
    name='Lecture 1',
    date=date.today()
)

# 3. Upload Image
image = Image.objects.create(
    session=session,
    original_image_path='/uploads/img1.jpg'
)

# 4. Process Image (after core logic)
image.mark_as_processed('/processed/img1.jpg')

# 5. Create Face Crops
crop1 = FaceCrop.objects.create(
    image=image,
    crop_image_path='/crops/face1.jpg',
    coordinates='100,100,150,150'
)
crop2 = FaceCrop.objects.create(
    image=image,
    crop_image_path='/crops/face2.jpg',
    coordinates='300,100,150,150'
)

# 6. Identify Students
crop1.identify_student(alice, confidence=0.95)
crop2.identify_student(bob, confidence=0.89)

# 7. Check Session Status
session.update_processing_status()
print(f"Session processed: {session.is_processed}")
```

### Attendance Queries

#### Get attendance for a student
```python
# Sessions attended
sessions = Session.objects.filter(
    images__face_crops__student=alice
).distinct().order_by('-date')

# Count
attendance_count = sessions.count()
```

#### Get present students in a session
```python
present = Student.objects.filter(
    face_crops__image__session=session
).distinct()

absent = Student.objects.filter(
    class_enrolled=session.class_session
).exclude(
    id__in=present.values_list('id', flat=True)
)
```

#### Calculate attendance rate
```python
total_sessions = cs_class.sessions.count()
attended_sessions = Session.objects.filter(
    images__face_crops__student=alice
).distinct().count()

rate = attended_sessions / total_sessions if total_sessions > 0 else 0
percentage = f"{rate * 100:.1f}%"
```

#### Get session statistics
```python
from django.db.models import Count

session_stats = Session.objects.filter(
    class_session=cs_class
).annotate(
    image_count=Count('images', distinct=True),
    face_count=Count('images__face_crops', distinct=True),
    identified_count=Count('images__face_crops', 
                          filter=Q(images__face_crops__is_identified=True),
                          distinct=True)
)
```

#### Get unidentified faces
```python
unidentified = FaceCrop.objects.filter(
    image__session=session,
    is_identified=False
)
```

## Field Reference

### Class Fields
| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| owner | FK(User) | Yes | - | CASCADE delete |
| name | CharField(255) | Yes | - | Min length 1 |
| description | TextField | No | '' | Can be blank |
| is_active | BooleanField | No | True | For archiving |
| created_at | DateTimeField | No | Auto | Auto-populated |
| updated_at | DateTimeField | No | Auto | Auto-updated |

### Student Fields
| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| class_enrolled | FK(Class) | Yes | - | CASCADE delete |
| first_name | CharField(150) | Yes | - | Min length 1 |
| last_name | CharField(150) | Yes | - | Min length 1 |
| student_id | CharField(50) | No | '' | Optional ID |
| email | EmailField | No | '' | Optional |
| created_at | DateTimeField | No | Auto | Auto-populated |

**Unique Constraint**: (first_name, last_name, class_enrolled)

### Session Fields
| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| class_session | FK(Class) | Yes | - | CASCADE delete |
| name | CharField(255) | Yes | - | Min length 1 |
| date | DateField | Yes | - | Session date |
| start_time | TimeField | No | None | Optional |
| end_time | TimeField | No | None | Optional |
| notes | TextField | No | '' | Can be blank |
| is_processed | BooleanField | No | False | Auto-updated |
| created_at | DateTimeField | No | Auto | Auto-populated |
| updated_at | DateTimeField | No | Auto | Auto-updated |

### Image Fields
| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| session | FK(Session) | Yes | - | CASCADE delete |
| original_image_path | CharField(500) | Yes | - | File path |
| processed_image_path | CharField(500) | No | '' | After processing |
| upload_date | DateTimeField | No | now() | Auto-set |
| is_processed | BooleanField | No | False | Processing flag |
| processing_date | DateTimeField | No | None | Set on processing |
| created_at | DateTimeField | No | Auto | Auto-populated |
| updated_at | DateTimeField | No | Auto | Auto-updated |

### FaceCrop Fields
| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| image | FK(Image) | Yes | - | CASCADE delete |
| student | FK(Student) | No | None | SET_NULL on delete |
| crop_image_path | CharField(500) | Yes | - | Crop file path |
| coordinates | CharField(255) | Yes | - | Format: "x,y,w,h" |
| confidence_score | FloatField | No | None | 0-1 range |
| is_identified | BooleanField | No | False | Identification flag |
| created_at | DateTimeField | No | Auto | Auto-populated |
| updated_at | DateTimeField | No | Auto | Auto-updated |

## Method Reference

### Class Methods
- `__str__()` → `"{name} ({owner.username})"`

### Student Methods
- `__str__()` → `"{first_name} {last_name}"`
- `full_name` (property) → `"{first_name} {last_name}"`

### Session Methods
- `__str__()` → `"{name} - {date}"`
- `update_processing_status()` → Updates `is_processed` based on images

### Image Methods
- `__str__()` → `"Image {id} - Session {session.name}"`
- `mark_as_processed(processed_path)` → Marks processed and updates session

### FaceCrop Methods
- `__str__()` → `"Crop {id} - {student.full_name}"` or `"Crop {id} - Unidentified"`
- `identify_student(student, confidence=None)` → Links to student
- `parse_coordinates()` → Returns dict `{'x': int, 'y': int, 'width': int, 'height': int}`
- `format_coordinates(x, y, width, height)` (static) → Returns `"x,y,width,height"`

## Django Admin URLs

- Classes: `/admin/attendance/class/`
- Students: `/admin/attendance/student/`
- Sessions: `/admin/attendance/session/`
- Images: `/admin/attendance/image/`
- Face Crops: `/admin/attendance/facecrop/`

## Testing

```bash
# Run all attendance tests
pytest attendance/tests/

# Run specific test file
pytest attendance/tests/test_models.py
pytest attendance/tests/test_integration.py

# Run with coverage
pytest --cov=attendance --cov-report=html

# Run specific test class
pytest attendance/tests/test_models.py::TestClassModel

# Run specific test
pytest attendance/tests/test_models.py::TestClassModel::test_create_class
```

## Import Statements

```python
# Models
from attendance.models import Class, Student, Session, Image, FaceCrop

# User model
from django.contrib.auth import get_user_model
User = get_user_model()

# DateTime utilities
from django.utils import timezone
from datetime import date, time, datetime, timedelta

# Database queries
from django.db.models import Q, Count, Avg, Max, Min, F, Prefetch

# Exceptions
from django.db import IntegrityError
from django.core.exceptions import ValidationError, ObjectDoesNotExist
```

## Tips & Tricks

### Prefetch Related Data
```python
# Efficient loading
classes = Class.objects.prefetch_related('students', 'sessions').filter(owner=user)
sessions = Session.objects.select_related('class_session').prefetch_related('images__face_crops')
```

### Bulk Create
```python
# Efficient for multiple objects
students = [
    Student(class_enrolled=cs_class, first_name=f'Student{i}', last_name='Test')
    for i in range(100)
]
Student.objects.bulk_create(students)
```

### Aggregate Queries
```python
from django.db.models import Count, Avg

stats = FaceCrop.objects.filter(is_identified=True).aggregate(
    total=Count('id'),
    avg_confidence=Avg('confidence_score')
)
```

### Complex Filters
```python
from django.db.models import Q

# OR conditions
recent_or_unprocessed = Session.objects.filter(
    Q(date__gte=date.today()) | Q(is_processed=False)
)

# AND conditions with exclude
active_with_students = Class.objects.filter(
    is_active=True,
    students__isnull=False
).distinct()
```
