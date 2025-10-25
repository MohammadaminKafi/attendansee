import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import date, time
from attendance.models import Class, Student, Session, Image, FaceCrop


User = get_user_model()


@pytest.mark.django_db
class TestClassModel:
    """Test cases for the Class model."""
    
    def test_create_class(self, user):
        """Test creating a class."""
        test_class = Class.objects.create(
            owner=user,
            name='Test Course',
            description='Test Description'
        )
        
        assert test_class.owner == user
        assert test_class.name == 'Test Course'
        assert test_class.description == 'Test Description'
        assert test_class.is_active is True
        assert test_class.created_at is not None
        assert test_class.updated_at is not None
    
    def test_class_string_representation(self, test_class, user):
        """Test the string representation of class."""
        assert str(test_class) == f"Introduction to Computer Science ({user.username})"
    
    def test_class_default_values(self, user):
        """Test default values for class fields."""
        test_class = Class.objects.create(
            owner=user,
            name='Minimal Course'
        )
        
        assert test_class.description == ''
        assert test_class.is_active is True
    
    def test_class_owner_cascade_delete(self, test_class, user):
        """Test that deleting a user deletes their classes."""
        class_id = test_class.id
        user.delete()
        
        assert not Class.objects.filter(id=class_id).exists()
    
    def test_user_can_have_multiple_classes(self, user):
        """Test that a user can own multiple classes."""
        class1 = Class.objects.create(owner=user, name='Course 1')
        class2 = Class.objects.create(owner=user, name='Course 2')
        
        assert user.classes.count() == 2
        assert class1 in user.classes.all()
        assert class2 in user.classes.all()
    
    def test_class_ordering(self, user):
        """Test that classes are ordered by creation date (newest first)."""
        class1 = Class.objects.create(owner=user, name='First Course')
        class2 = Class.objects.create(owner=user, name='Second Course')
        
        classes = Class.objects.all()
        assert classes[0] == class2
        assert classes[1] == class1
    
    def test_class_name_validation(self, user):
        """Test that class name cannot be empty."""
        
        test_class = Class(owner=user, name='')
        with pytest.raises(ValidationError):
            test_class.full_clean()


@pytest.mark.django_db
class TestStudentModel:
    """Test cases for the Student model."""
    
    def test_create_student(self, test_class):
        """Test creating a student."""
        student = Student.objects.create(
            class_enrolled=test_class,
            first_name='John',
            last_name='Doe',
            student_id='S123',
            email='john@example.com'
        )
        
        assert student.class_enrolled == test_class
        assert student.first_name == 'John'
        assert student.last_name == 'Doe'
        assert student.student_id == 'S123'
        assert student.email == 'john@example.com'
        assert student.created_at is not None
    
    def test_student_string_representation(self, student1):
        """Test the string representation of student."""
        assert str(student1) == 'Alice Johnson'
    
    def test_student_full_name_property(self, student1):
        """Test the full_name property."""
        assert student1.full_name == 'Alice Johnson'
    
    def test_student_default_values(self, test_class):
        """Test default values for student fields."""
        student = Student.objects.create(
            class_enrolled=test_class,
            first_name='Jane',
            last_name='Smith'
        )
        
        assert student.student_id == ''
        assert student.email == ''
    
    def test_student_unique_constraint(self, test_class):
        """Test that students must be unique by first_name, last_name, and class."""
        Student.objects.create(
            class_enrolled=test_class,
            first_name='John',
            last_name='Doe'
        )
        
        with pytest.raises(IntegrityError):
            Student.objects.create(
                class_enrolled=test_class,
                first_name='John',
                last_name='Doe'
            )
    
    def test_same_student_different_classes(self, test_class, another_class):
        """Test that the same student name can exist in different classes."""
        student1 = Student.objects.create(
            class_enrolled=test_class,
            first_name='John',
            last_name='Doe'
        )
        student2 = Student.objects.create(
            class_enrolled=another_class,
            first_name='John',
            last_name='Doe'
        )
        
        assert student1.id != student2.id
        assert Student.objects.filter(first_name='John', last_name='Doe').count() == 2
    
    def test_student_cascade_delete_with_class(self, student1, test_class):
        """Test that deleting a class deletes its students."""
        student_id = student1.id
        test_class.delete()
        
        assert not Student.objects.filter(id=student_id).exists()
    
    def test_student_ordering(self, test_class):
        """Test that students are ordered by last name, then first name."""
        student_z = Student.objects.create(
            class_enrolled=test_class,
            first_name='Zoe',
            last_name='Adams'
        )
        student_a = Student.objects.create(
            class_enrolled=test_class,
            first_name='Alice',
            last_name='Adams'
        )
        
        students = Student.objects.filter(class_enrolled=test_class)
        assert students[0] == student_a
        assert students[1] == student_z
    
    def test_student_name_validation(self, test_class):
        """Test that student first_name and last_name cannot be empty."""
        from django.core.exceptions import ValidationError
        
        # Test empty first_name
        student1 = Student(
            class_enrolled=test_class,
            first_name='',
            last_name='Doe'
        )
        with pytest.raises(ValidationError):
            student1.full_clean()
        
        # Test empty last_name
        student2 = Student(
            class_enrolled=test_class,
            first_name='John',
            last_name=''
        )
        with pytest.raises(ValidationError):
            student2.full_clean()


@pytest.mark.django_db
class TestSessionModel:
    """Test cases for the Session model."""
    
    def test_create_session(self, test_class):
        """Test creating a session."""
        session = Session.objects.create(
            class_session=test_class,
            name='Week 1',
            date=date(2025, 10, 15),
            start_time=time(10, 0),
            end_time=time(11, 30),
            notes='First lecture'
        )
        
        assert session.class_session == test_class
        assert session.name == 'Week 1'
        assert session.date == date(2025, 10, 15)
        assert session.start_time == time(10, 0)
        assert session.end_time == time(11, 30)
        assert session.notes == 'First lecture'
        assert session.is_processed is False
        assert session.created_at is not None
        assert session.updated_at is not None
    
    def test_session_string_representation(self, session1):
        """Test the string representation of session."""
        assert str(session1) == 'Week 1 - Introduction - 2025-10-15'
    
    def test_session_default_values(self, test_class):
        """Test default values for session fields."""
        session = Session.objects.create(
            class_session=test_class,
            name='Test Session',
            date=date.today()
        )
        
        assert session.start_time is None
        assert session.end_time is None
        assert session.notes == ''
        assert session.is_processed is False
    
    def test_session_cascade_delete_with_class(self, session1, test_class):
        """Test that deleting a class deletes its sessions."""
        session_id = session1.id
        test_class.delete()
        
        assert not Session.objects.filter(id=session_id).exists()
    
    def test_session_ordering(self, test_class):
        """Test that sessions are ordered by date (newest first)."""
        session1 = Session.objects.create(
            class_session=test_class,
            name='Earlier',
            date=date(2025, 10, 10)
        )
        session2 = Session.objects.create(
            class_session=test_class,
            name='Later',
            date=date(2025, 10, 20)
        )
        
        sessions = Session.objects.filter(class_session=test_class)
        assert sessions[0] == session2
        assert sessions[1] == session1
    
    def test_update_processing_status_no_images(self, session1):
        """Test update_processing_status with no images."""
        session1.update_processing_status()
        assert session1.is_processed is False
    
    def test_update_processing_status_partial_processing(self, session1, image1, image2):
        """Test update_processing_status with some images processed."""
        image1.is_processed = True
        image1.save()
        
        session1.update_processing_status()
        assert session1.is_processed is False
    
    def test_update_processing_status_all_processed(self, session1, image1, image2):
        """Test update_processing_status with all images processed."""
        image1.is_processed = True
        image1.save()
        image2.is_processed = True
        image2.save()
        
        session1.update_processing_status()
        assert session1.is_processed is True
    
    def test_session_name_validation(self, test_class):
        """Test that session name cannot be empty."""
        from django.core.exceptions import ValidationError
        
        session = Session(
            class_session=test_class,
            name='',
            date=date.today()
        )
        with pytest.raises(ValidationError):
            session.full_clean()


@pytest.mark.django_db
class TestImageModel:
    """Test cases for the Image model."""
    
    def test_create_image(self, session1):
        """Test creating an image."""
        upload_time = timezone.now()
        image = Image.objects.create(
            session=session1,
            original_image_path='/path/to/image.jpg',
            upload_date=upload_time
        )
        
        assert image.session == session1
        assert image.original_image_path == '/path/to/image.jpg'
        # ImageField with default='' returns an empty string, but we need to check .name
        assert not image.processed_image_path or image.processed_image_path.name == ''
        assert image.upload_date == upload_time
        assert image.is_processed is False
        assert image.processing_date is None
        assert image.created_at is not None
        assert image.updated_at is not None
    
    def test_image_string_representation(self, image1, session1):
        """Test the string representation of image."""
        expected = f"Image {image1.id} - Session {session1.name}"
        assert str(image1) == expected
    
    def test_image_default_values(self, session1):
        """Test default values for image fields."""
        image = Image.objects.create(
            session=session1,
            original_image_path='/path/to/image.jpg'
        )
        
        # ImageField with default='' returns an empty string, but we need to check .name
        assert not image.processed_image_path or image.processed_image_path.name == ''
        assert image.is_processed is False
        assert image.processing_date is None
        assert image.upload_date is not None  # Has default=timezone.now
    
    def test_image_cascade_delete_with_session(self, image1, session1):
        """Test that deleting a session deletes its images."""
        image_id = image1.id
        session1.delete()
        
        assert not Image.objects.filter(id=image_id).exists()
    
    def test_image_ordering(self, session1):
        """Test that images are ordered by upload date (newest first)."""
        image1 = Image.objects.create(
            session=session1,
            original_image_path='/path/1.jpg',
            upload_date=timezone.now()
        )
        # Create a slightly later image
        import time
        time.sleep(0.01)  # Ensure different timestamp
        image2 = Image.objects.create(
            session=session1,
            original_image_path='/path/2.jpg',
            upload_date=timezone.now()
        )
        
        images = Image.objects.filter(session=session1)
        assert images[0] == image2
        assert images[1] == image1
    
    def test_mark_as_processed(self, image1, session1):
        """Test mark_as_processed method."""
        processed_path = '/path/to/processed.jpg'
        image1.mark_as_processed(processed_path)
        
        image1.refresh_from_db()
        assert image1.is_processed is True
        assert image1.processed_image_path == processed_path
        assert image1.processing_date is not None
    
    def test_mark_as_processed_updates_session(self, session1, image1, image2):
        """Test that marking all images as processed updates session status."""
        image1.mark_as_processed('/path/1.jpg')
        session1.refresh_from_db()
        assert session1.is_processed is False
        
        image2.mark_as_processed('/path/2.jpg')
        session1.refresh_from_db()
        assert session1.is_processed is True


@pytest.mark.django_db
class TestFaceCropModel:
    """Test cases for the FaceCrop model."""
    
    def test_create_face_crop_with_student(self, image1, student1):
        """Test creating an identified face crop."""
        crop = FaceCrop.objects.create(
            image=image1,
            student=student1,
            crop_image_path='/path/to/crop.jpg',
            coordinates='100,150,200,250',
            confidence_score=0.92,
            is_identified=True
        )
        
        assert crop.image == image1
        assert crop.student == student1
        assert crop.crop_image_path == '/path/to/crop.jpg'
        assert crop.coordinates == '100,150,200,250'
        assert crop.confidence_score == 0.92
        assert crop.is_identified is True
        assert crop.created_at is not None
        assert crop.updated_at is not None
    
    def test_create_face_crop_without_student(self, image1):
        """Test creating an unidentified face crop."""
        crop = FaceCrop.objects.create(
            image=image1,
            crop_image_path='/path/to/crop.jpg',
            coordinates='100,150,200,250'
        )
        
        assert crop.image == image1
        assert crop.student is None
        assert crop.confidence_score is None
        assert crop.is_identified is False
    
    def test_face_crop_string_representation_identified(self, face_crop1):
        """Test the string representation of identified face crop."""
        expected = f"Crop {face_crop1.id} - Alice Johnson"
        assert str(face_crop1) == expected
    
    def test_face_crop_string_representation_unidentified(self, face_crop2):
        """Test the string representation of unidentified face crop."""
        expected = f"Crop {face_crop2.id} - Unidentified"
        assert str(face_crop2) == expected
    
    def test_face_crop_cascade_delete_with_image(self, face_crop1, image1):
        """Test that deleting an image deletes its face crops."""
        crop_id = face_crop1.id
        image1.delete()
        
        assert not FaceCrop.objects.filter(id=crop_id).exists()
    
    def test_face_crop_set_null_on_student_delete(self, face_crop1, student1):
        """Test that deleting a student sets face crop student to null."""
        crop_id = face_crop1.id
        student1.delete()
        
        crop = FaceCrop.objects.get(id=crop_id)
        assert crop.student is None
    
    def test_identify_student(self, face_crop2, student1):
        """Test identify_student method."""
        face_crop2.identify_student(student1, confidence=0.88)
        
        face_crop2.refresh_from_db()
        assert face_crop2.student == student1
        assert face_crop2.is_identified is True
        assert face_crop2.confidence_score == 0.88
    
    def test_identify_student_without_confidence(self, face_crop2, student1):
        """Test identify_student method without confidence score."""
        face_crop2.identify_student(student1)
        
        face_crop2.refresh_from_db()
        assert face_crop2.student == student1
        assert face_crop2.is_identified is True
        assert face_crop2.confidence_score is None
    
    def test_parse_coordinates(self, face_crop1):
        """Test parse_coordinates method."""
        coords = face_crop1.parse_coordinates()
        
        assert coords == {
            'x': 100,
            'y': 150,
            'width': 200,
            'height': 250
        }
    
    def test_parse_coordinates_invalid(self, image1):
        """Test parse_coordinates with invalid data."""
        crop = FaceCrop.objects.create(
            image=image1,
            crop_image_path='/path/to/crop.jpg',
            coordinates='invalid'
        )
        
        coords = crop.parse_coordinates()
        assert coords is None
    
    def test_format_coordinates(self):
        """Test format_coordinates static method."""
        formatted = FaceCrop.format_coordinates(100, 150, 200, 250)
        assert formatted == '100,150,200,250'
    
    def test_face_crop_ordering(self, image1):
        """Test that face crops are ordered by creation date (newest first)."""
        crop1 = FaceCrop.objects.create(
            image=image1,
            crop_image_path='/path/1.jpg',
            coordinates='10,10,50,50'
        )
        crop2 = FaceCrop.objects.create(
            image=image1,
            crop_image_path='/path/2.jpg',
            coordinates='20,20,60,60'
        )
        
        crops = FaceCrop.objects.filter(image=image1)
        assert crops[0] == crop2
        assert crops[1] == crop1


@pytest.mark.django_db
class TestModelRelationships:
    """Test cases for model relationships and cascading effects."""
    
    def test_user_to_classes_relationship(self, user, test_class, another_class):
        """Test user can access their classes through reverse relation."""
        classes = user.classes.all()
        assert classes.count() == 2
        assert test_class in classes
        assert another_class in classes
    
    def test_class_to_students_relationship(self, test_class, student1, student2):
        """Test class can access its students."""
        students = test_class.students.all()
        assert students.count() == 2
        assert student1 in students
        assert student2 in students
    
    def test_class_to_sessions_relationship(self, test_class, session1, session2):
        """Test class can access its sessions."""
        sessions = test_class.sessions.all()
        assert sessions.count() == 2
        assert session1 in sessions
        assert session2 in sessions
    
    def test_session_to_images_relationship(self, session1, image1, image2):
        """Test session can access its images."""
        images = session1.images.all()
        assert images.count() == 2
        assert image1 in images
        assert image2 in images
    
    def test_image_to_face_crops_relationship(self, image1, face_crop1, face_crop2):
        """Test image can access its face crops."""
        crops = image1.face_crops.all()
        assert crops.count() == 2
        assert face_crop1 in crops
        assert face_crop2 in crops
    
    def test_student_to_face_crops_relationship(self, student1, face_crop1):
        """Test student can access their face crops."""
        crops = student1.face_crops.all()
        assert crops.count() == 1
        assert face_crop1 in crops
    
    def test_cascade_delete_user_to_all_related(self, user, test_class, student1, session1, image1, face_crop1):
        """Test cascade delete from user down to all related objects."""
        class_id = test_class.id
        student_id = student1.id
        session_id = session1.id
        image_id = image1.id
        crop_id = face_crop1.id
        
        user.delete()
        
        assert not Class.objects.filter(id=class_id).exists()
        assert not Student.objects.filter(id=student_id).exists()
        assert not Session.objects.filter(id=session_id).exists()
        assert not Image.objects.filter(id=image_id).exists()
        assert not FaceCrop.objects.filter(id=crop_id).exists()
    
    def test_face_crop_persists_after_student_delete(self, face_crop1, student1):
        """Test that face crops are not deleted when student is deleted."""
        crop_id = face_crop1.id
        student1.delete()
        
        crop = FaceCrop.objects.get(id=crop_id)
        assert crop.student is None
        assert crop.is_identified is True  # Still marked as identified
