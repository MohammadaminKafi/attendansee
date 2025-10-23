import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, time
from rest_framework.test import APIClient
from attendance.models import Class, Student, Session, Image, FaceCrop


User = get_user_model()


@pytest.fixture
def api_client():
    """Fixture to provide an API client for tests."""
    return APIClient()


@pytest.fixture
def user(db):
    """Fixture to create a regular user (professor)."""
    return User.objects.create_user(
        username='professor',
        email='professor@example.com',
        password='testpass123',
        first_name='John',
        last_name='Doe'
    )


@pytest.fixture
def another_user(db):
    """Fixture to create another user."""
    return User.objects.create_user(
        username='professor2',
        email='professor2@example.com',
        password='testpass123',
        first_name='Jane',
        last_name='Smith'
    )


@pytest.fixture
def admin_user(db):
    """Fixture to create an admin user."""
    return User.objects.create_user(
        username='admin',
        email='admin@example.com',
        password='adminpass123',
        first_name='Admin',
        last_name='User',
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def authenticated_client(api_client, user):
    """Fixture to provide an authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def another_authenticated_client(api_client, another_user):
    """Fixture to provide an authenticated API client for another user."""
    api_client.force_authenticate(user=another_user)
    return api_client


@pytest.fixture
def admin_authenticated_client(api_client, admin_user):
    """Fixture to provide an admin authenticated API client."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def test_class(db, user):
    """Fixture to create a class."""
    return Class.objects.create(
        owner=user,
        name='Introduction to Computer Science',
        description='A beginner course in computer science',
        is_active=True
    )


@pytest.fixture
def another_class(db, user):
    """Fixture to create another class for the same user."""
    return Class.objects.create(
        owner=user,
        name='Advanced Algorithms',
        description='Advanced course on algorithms',
        is_active=True
    )


@pytest.fixture
def inactive_class(db, user):
    """Fixture to create an inactive class."""
    return Class.objects.create(
        owner=user,
        name='Old Course',
        description='This course is archived',
        is_active=False
    )


@pytest.fixture
def student1(db, test_class):
    """Fixture to create a student."""
    return Student.objects.create(
        class_enrolled=test_class,
        first_name='Alice',
        last_name='Johnson',
        student_id='S001',
        email='alice@example.com'
    )


@pytest.fixture
def student2(db, test_class):
    """Fixture to create another student in the same class."""
    return Student.objects.create(
        class_enrolled=test_class,
        first_name='Bob',
        last_name='Williams',
        student_id='S002',
        email='bob@example.com'
    )


@pytest.fixture
def student3(db, another_class):
    """Fixture to create a student in a different class."""
    return Student.objects.create(
        class_enrolled=another_class,
        first_name='Alice',
        last_name='Johnson',
        student_id='S003',
        email='alice2@example.com'
    )


@pytest.fixture
def session1(db, test_class):
    """Fixture to create a session."""
    return Session.objects.create(
        class_session=test_class,
        name='Week 1 - Introduction',
        date=date(2025, 10, 15),
        start_time=time(10, 0),
        end_time=time(11, 30),
        notes='First lecture of the semester'
    )


@pytest.fixture
def session2(db, test_class):
    """Fixture to create another session."""
    return Session.objects.create(
        class_session=test_class,
        name='Week 2 - Data Structures',
        date=date(2025, 10, 22),
        start_time=time(10, 0),
        end_time=time(11, 30)
    )


@pytest.fixture
def image1(db, session1):
    """Fixture to create an image."""
    return Image.objects.create(
        session=session1,
        original_image_path='/path/to/images/session1_img1.jpg',
        upload_date=timezone.now()
    )


@pytest.fixture
def image2(db, session1):
    """Fixture to create another image in the same session."""
    return Image.objects.create(
        session=session1,
        original_image_path='/path/to/images/session1_img2.jpg',
        upload_date=timezone.now()
    )


@pytest.fixture
def processed_image(db, session1):
    """Fixture to create a processed image."""
    return Image.objects.create(
        session=session1,
        original_image_path='/path/to/images/session1_img3.jpg',
        processed_image_path='/path/to/processed/session1_img3.jpg',
        is_processed=True,
        processing_date=timezone.now(),
        upload_date=timezone.now()
    )


@pytest.fixture
def face_crop1(db, image1, student1):
    """Fixture to create an identified face crop."""
    return FaceCrop.objects.create(
        image=image1,
        student=student1,
        crop_image_path='/path/to/crops/crop1.jpg',
        coordinates='100,150,200,250',
        confidence_score=0.95,
        is_identified=True
    )


@pytest.fixture
def face_crop2(db, image1):
    """Fixture to create an unidentified face crop."""
    return FaceCrop.objects.create(
        image=image1,
        crop_image_path='/path/to/crops/crop2.jpg',
        coordinates='300,200,180,220',
        is_identified=False
    )


@pytest.fixture
def face_crop3(db, processed_image, student2):
    """Fixture to create another identified face crop."""
    return FaceCrop.objects.create(
        image=processed_image,
        student=student2,
        crop_image_path='/path/to/crops/crop3.jpg',
        coordinates='50,75,150,175',
        confidence_score=0.89,
        is_identified=True
    )
