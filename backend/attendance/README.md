# Attendance App

This Django app manages the core attendance tracking functionality for AttendanSee, including classes, students, sessions, images, and face recognition.

## Models

### Class
Represents a class/course taught by a professor.

**Fields:**
- `owner` (ForeignKey to User): The professor who owns this class
- `name` (CharField): Name of the class
- `description` (TextField): Optional description
- `is_active` (BooleanField): Whether the class is currently active (for archiving)
- `created_at` (DateTimeField): Auto-populated creation timestamp
- `updated_at` (DateTimeField): Auto-updated modification timestamp

**Relationships:**
- Has many `Student` objects (students enrolled)
- Has many `Session` objects (attendance sessions)
- Belongs to one `User` (owner/professor)

**Constraints:**
- Indexed on `owner` and `created_at` for efficient queries
- Ordered by creation date (newest first)

---

### Student
Represents a student enrolled in a class.

**Fields:**
- `class_enrolled` (ForeignKey to Class): The class this student is enrolled in
- `first_name` (CharField): Student's first name
- `last_name` (CharField): Student's last name
- `student_id` (CharField): Optional unique student identifier
- `email` (EmailField): Optional student email
- `created_at` (DateTimeField): Auto-populated creation timestamp

**Relationships:**
- Belongs to one `Class`
- Has many `FaceCrop` objects (face detections in images)

**Constraints:**
- Unique constraint on (`first_name`, `last_name`, `class_enrolled`)
- The same student name can exist in different classes
- Ordered by last name, then first name

**Properties:**
- `full_name`: Returns "{first_name} {last_name}"

---

### Session
Represents an attendance session for a class (e.g., a single lecture).

**Fields:**
- `class_session` (ForeignKey to Class): The class this session belongs to
- `name` (CharField): Name/title of the session
- `date` (DateField): Date of the session
- `start_time` (TimeField): Optional start time
- `end_time` (TimeField): Optional end time
- `notes` (TextField): Optional notes about the session
- `is_processed` (BooleanField): Whether all images have been processed
- `created_at` (DateTimeField): Auto-populated creation timestamp
- `updated_at` (DateTimeField): Auto-updated modification timestamp

**Relationships:**
- Belongs to one `Class`
- Has many `Image` objects (photos taken during the session)

**Constraints:**
- Indexed on `class_session` and `date` for efficient queries
- Ordered by date (newest first)

**Methods:**
- `update_processing_status()`: Updates `is_processed` based on whether all images are processed

---

### Image
Represents an image taken during a session.

**Fields:**
- `session` (ForeignKey to Session): The session this image belongs to
- `original_image_path` (CharField): Path to the original uploaded image
- `processed_image_path` (CharField): Path to the processed image (with face rectangles)
- `upload_date` (DateTimeField): When the image was uploaded
- `is_processed` (BooleanField): Whether face detection has been performed
- `processing_date` (DateTimeField): When the image was processed
- `created_at` (DateTimeField): Auto-populated creation timestamp
- `updated_at` (DateTimeField): Auto-updated modification timestamp

**Relationships:**
- Belongs to one `Session`
- Has many `FaceCrop` objects (detected faces)

**Constraints:**
- Indexed on `session` and `upload_date` for efficient queries
- Ordered by upload date (newest first)

**Methods:**
- `mark_as_processed(processed_path)`: Marks the image as processed and updates the session status

---

### FaceCrop
Represents a detected face crop from an image.

**Fields:**
- `image` (ForeignKey to Image): The image this crop belongs to
- `student` (ForeignKey to Student, nullable): The identified student (null if unidentified)
- `crop_image_path` (CharField): Path to the cropped face image
- `coordinates` (CharField): Face position as "x,y,width,height"
- `confidence_score` (FloatField, nullable): Confidence of student identification (0-1)
- `is_identified` (BooleanField): Whether the face has been identified
- `created_at` (DateTimeField): Auto-populated creation timestamp
- `updated_at` (DateTimeField): Auto-updated modification timestamp

**Relationships:**
- Belongs to one `Image`
- Belongs to one `Student` (nullable, SET_NULL on delete)

**Constraints:**
- Indexed on `image`, `student`, and `is_identified` for efficient queries
- Ordered by creation date (newest first)
- Student deletion sets the reference to NULL (preserves crop data)

**Methods:**
- `identify_student(student, confidence=None)`: Links the crop to a student
- `parse_coordinates()`: Parses coordinate string into dict with x, y, width, height
- `format_coordinates(x, y, width, height)`: Static method to format coordinates

---

## Database Design Decisions

### Cascade Deletes
- **User → Class → Student, Session → Image → FaceCrop**: Full cascade delete
  - Deleting a user removes all their classes and related data
  - This ensures data integrity and prevents orphaned records

### SET_NULL
- **Student → FaceCrop**: SET_NULL on delete
  - When a student is deleted, their face crops remain for historical data
  - This allows reviewing/reassigning unidentified faces later

### Unique Constraints
- **Student**: Unique on (first_name, last_name, class_enrolled)
  - Prevents duplicate student entries in the same class
  - Same student name can exist in different classes

### Indexes
Strategic indexes for common query patterns:
- Classes by owner and date
- Students by class and name
- Sessions by class and date
- Images by session
- Face crops by image, student, and identification status

## Usage Examples

### Creating a Complete Workflow

```python
from django.contrib.auth import get_user_model
from attendance.models import Class, Student, Session, Image, FaceCrop

User = get_user_model()

# 1. Professor creates a class
professor = User.objects.get(username='prof_smith')
cs_class = Class.objects.create(
    owner=professor,
    name='Computer Science 101',
    description='Introduction to Computer Science'
)

# 2. Add students
alice = Student.objects.create(
    class_enrolled=cs_class,
    first_name='Alice',
    last_name='Johnson',
    student_id='CS001',
    email='alice@example.com'
)

# 3. Create a session
session = Session.objects.create(
    class_session=cs_class,
    name='Week 1 - Introduction',
    date='2025-10-22'
)

# 4. Upload and process an image
image = Image.objects.create(
    session=session,
    original_image_path='/uploads/session1_img1.jpg'
)
image.mark_as_processed('/processed/session1_img1.jpg')

# 5. Create face crops
crop = FaceCrop.objects.create(
    image=image,
    crop_image_path='/crops/crop1.jpg',
    coordinates=FaceCrop.format_coordinates(100, 150, 200, 250)
)

# 6. Identify student
crop.identify_student(alice, confidence=0.95)
```

### Querying Attendance

```python
# Get all sessions a student attended
sessions_attended = Session.objects.filter(
    images__face_crops__student=alice
).distinct()

# Get all students present in a session
present_students = Student.objects.filter(
    face_crops__image__session=session
).distinct()

# Get unidentified face crops
unidentified = FaceCrop.objects.filter(is_identified=False)

# Calculate attendance rate
total_sessions = cs_class.sessions.count()
attended_sessions = Session.objects.filter(
    images__face_crops__student=alice
).distinct().count()
attendance_rate = attended_sessions / total_sessions if total_sessions > 0 else 0
```

## Testing

Comprehensive test suite included in `attendance/tests/`:

- `test_models.py`: Unit tests for each model
- `test_integration.py`: Integration tests for complete workflows
- `conftest.py`: Pytest fixtures for test data

Run tests with:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=attendance --cov-report=html
```

---

## Embeddings

This app generates face embeddings using DeepFace. Only 512-dimensional models are supported:

- arcface → ArcFace (512D)
- facenet512 → FaceNet512 (512D)

Notes:
- 128D FaceNet is not supported anymore. Existing records that were generated with a 128D model remain readable but are considered deprecated.
- Embedding vectors are stored in a pgvector field with 512 dimensions and are used for similarity search and clustering.
