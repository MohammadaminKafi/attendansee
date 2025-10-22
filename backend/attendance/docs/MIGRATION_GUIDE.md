# Migration Guide for Attendance App

## Prerequisites

Before running migrations, ensure:
1. PostgreSQL database is running
2. Database credentials in `settings.py` are correct
3. Virtual environment is activated
4. All dependencies are installed

## Migration Commands

### 1. Create Initial Migrations

```bash
cd backend
python manage.py makemigrations attendance
```

Expected output:
```
Migrations for 'attendance':
  attendance/migrations/0001_initial.py
    - Create model Class
    - Create model Student
    - Create model Session
    - Create model Image
    - Create model FaceCrop
    - Add constraint unique_student_per_class on model student
```

### 2. Apply Migrations

```bash
python manage.py migrate attendance
```

Expected output:
```
Running migrations:
  Applying attendance.0001_initial... OK
```

### 3. Verify Migrations

Check migration status:
```bash
python manage.py showmigrations attendance
```

Expected output:
```
attendance
 [X] 0001_initial
```

## Database Tables Created

After migration, the following tables will be created:

1. `classes` - Class model
2. `students` - Student model with unique constraint
3. `sessions` - Session model
4. `images` - Image model
5. `face_crops` - FaceCrop model

Plus indexes:
- 5 tables × multiple indexes each
- See DATABASE_SCHEMA.md for details

## Post-Migration Steps

### 1. Create Superuser (if not already created)

```bash
python manage.py createsuperuser
```

### 2. Test Admin Interface

```bash
python manage.py runserver
```

Visit: http://localhost:8000/admin

You should see:
- Authentication (Users, Groups)
- Attendance (Classes, Students, Sessions, Images, Face Crops)

### 3. Run Tests

```bash
pytest
```

Expected: All tests should pass

### 4. Test Model Creation

Open Django shell:
```bash
python manage.py shell
```

Test basic model creation:
```python
from django.contrib.auth import get_user_model
from attendance.models import Class, Student, Session, Image, FaceCrop
from datetime import date

User = get_user_model()

# Create or get a user
user = User.objects.first() or User.objects.create_user(
    username='testprof',
    email='prof@test.com',
    password='test123'
)

# Create a class
cs_class = Class.objects.create(
    owner=user,
    name='Test Class',
    description='Testing model creation'
)

# Create a student
student = Student.objects.create(
    class_enrolled=cs_class,
    first_name='Test',
    last_name='Student',
    student_id='T001'
)

# Create a session
session = Session.objects.create(
    class_session=cs_class,
    name='Test Session',
    date=date.today()
)

# Create an image
image = Image.objects.create(
    session=session,
    original_image_path='/test/image.jpg'
)

# Create a face crop
crop = FaceCrop.objects.create(
    image=image,
    crop_image_path='/test/crop.jpg',
    coordinates='100,100,150,150'
)

# Verify relationships
print(f"Class: {cs_class}")
print(f"Students: {cs_class.students.count()}")
print(f"Sessions: {cs_class.sessions.count()}")
print(f"Images: {session.images.count()}")
print(f"Crops: {image.face_crops.count()}")
```

## Troubleshooting

### Issue: Database Connection Error

**Error:**
```
django.db.utils.OperationalError: could not connect to server
```

**Solution:**
1. Check PostgreSQL is running
2. Verify database credentials in settings.py
3. Ensure database exists:
   ```sql
   CREATE DATABASE attendansee_db;
   ```

### Issue: Migration Conflicts

**Error:**
```
Conflicting migrations detected
```

**Solution:**
```bash
python manage.py makemigrations --merge
python manage.py migrate
```

### Issue: Migration Already Applied

**Error:**
```
Migration attendance.0001_initial is applied before its dependency
```

**Solution:**
1. Check migration dependencies
2. If needed, reset migrations (DANGER - loses data):
   ```bash
   python manage.py migrate attendance zero
   rm attendance/migrations/0001_*.py
   python manage.py makemigrations attendance
   python manage.py migrate attendance
   ```

### Issue: Constraint Violation During Test

**Error:**
```
IntegrityError: duplicate key value violates unique constraint
```

**Solution:**
- This is expected for unique constraint tests
- Tests should use `pytest.raises(IntegrityError)` to catch this
- If occurring in production, check for duplicate data

## Rollback

### Rollback Last Migration
```bash
python manage.py migrate attendance zero
```

### Delete Migration Files
```bash
rm attendance/migrations/0001_*.py
```

### Recreate Migrations
```bash
python manage.py makemigrations attendance
python manage.py migrate attendance
```

## Database Schema Check

### View SQL for Migration

```bash
python manage.py sqlmigrate attendance 0001
```

This shows the actual SQL that will be executed.

### Inspect Database

Using PostgreSQL CLI:
```bash
psql -U attendansee_user -d attendansee_db
```

Check tables:
```sql
\dt
```

Check table structure:
```sql
\d classes
\d students
\d sessions
\d images
\d face_crops
```

Check constraints:
```sql
SELECT conname, contype 
FROM pg_constraint 
WHERE conrelid = 'students'::regclass;
```

Check indexes:
```sql
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'classes';
```

## Testing After Migration

### Run Full Test Suite
```bash
pytest
```

### Run Specific Tests
```bash
pytest attendance/tests/test_models.py
pytest attendance/tests/test_integration.py
```

### Run with Coverage
```bash
pytest --cov=attendance --cov-report=html
```

View coverage report:
```bash
# Open in browser
htmlcov/index.html
```

## Next Steps After Successful Migration

1. ✅ Models are ready
2. ✅ Tests are passing
3. ✅ Admin interface is working

Next development tasks:
1. Create serializers for API endpoints
2. Build API views (ListCreateAPIView, RetrieveUpdateDestroyAPIView)
3. Define URL patterns
4. Add permissions (IsOwner, IsAuthenticated)
5. Implement file upload handling
6. Integrate with core face detection logic
7. Add API documentation (swagger/redoc)
8. Build frontend integration

## Migration Best Practices

1. **Always backup before migration**
   ```bash
   pg_dump attendansee_db > backup_$(date +%Y%m%d).sql
   ```

2. **Test migrations on development first**
   - Never run untested migrations in production

3. **Keep migrations small**
   - One logical change per migration
   - Easier to debug and rollback

4. **Review SQL before applying**
   ```bash
   python manage.py sqlmigrate attendance 0001
   ```

5. **Document schema changes**
   - Keep DATABASE_SCHEMA.md updated
   - Note breaking changes

6. **Use migrations for data too**
   - Use data migrations for initial data
   - Keep schema and data in sync

## Useful Commands Reference

```bash
# Check migration plan
python manage.py migrate --plan

# Show migrations
python manage.py showmigrations

# Create empty migration (for data migrations)
python manage.py makemigrations --empty attendance

# Run specific migration
python manage.py migrate attendance 0001

# Check for migration issues
python manage.py makemigrations --check --dry-run

# Show SQL for migration
python manage.py sqlmigrate attendance 0001

# Run tests
pytest
pytest --cov=attendance
pytest -v -s  # verbose with print statements

# Shell access
python manage.py shell
python manage.py shell_plus  # if django-extensions installed

# Database shell
python manage.py dbshell
```
