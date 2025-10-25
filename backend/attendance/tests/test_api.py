import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from datetime import date, time
from attendance.models import Class, Student, Session, Image, FaceCrop


User = get_user_model()


@pytest.mark.django_db
class TestClassAPI:
    """Test cases for Class API endpoints."""
    
    def test_list_classes_authenticated(self, authenticated_client, user):
        """Test listing classes for authenticated user."""
        # Create classes for the user
        Class.objects.create(owner=user, name='CS 101')
        Class.objects.create(owner=user, name='Math 101')
        
        url = reverse('attendance:class-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
    
    def test_list_classes_unauthenticated(self, api_client):
        """Test that unauthenticated users cannot list classes."""
        url = reverse('attendance:class-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_class(self, authenticated_client):
        """Test creating a class."""
        url = reverse('attendance:class-list')
        data = {
            'name': 'Physics 101',
            'description': 'Introduction to Physics',
            'is_active': True
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Physics 101'
        assert response.data['description'] == 'Introduction to Physics'
        assert 'owner' in response.data
    
    def test_retrieve_class(self, authenticated_client, user):
        """Test retrieving a specific class."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        
        url = reverse('attendance:class-detail', kwargs={'pk': test_class.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'CS 101'
        assert 'student_count' in response.data
        assert 'session_count' in response.data
    
    def test_update_class(self, authenticated_client, user):
        """Test updating a class."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        
        url = reverse('attendance:class-detail', kwargs={'pk': test_class.pk})
        data = {
            'name': 'CS 102',
            'description': 'Updated description',
            'is_active': False
        }
        response = authenticated_client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'CS 102'
        assert response.data['description'] == 'Updated description'
        assert response.data['is_active'] is False
    
    def test_partial_update_class(self, authenticated_client, user):
        """Test partially updating a class."""
        test_class = Class.objects.create(owner=user, name='CS 101', description='Old desc')
        
        url = reverse('attendance:class-detail', kwargs={'pk': test_class.pk})
        data = {'description': 'New description'}
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'CS 101'  # Unchanged
        assert response.data['description'] == 'New description'
    
    def test_delete_class(self, authenticated_client, user):
        """Test deleting a class."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        
        url = reverse('attendance:class-detail', kwargs={'pk': test_class.pk})
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Class.objects.filter(pk=test_class.pk).exists()
    
    def test_cannot_access_other_user_class(self, authenticated_client, another_user):
        """Test that users cannot access classes owned by others."""
        other_class = Class.objects.create(owner=another_user, name='Other Class')
        
        url = reverse('attendance:class-detail', kwargs={'pk': other_class.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_admin_can_access_all_classes(self, admin_authenticated_client, user, another_user):
        """Test that admin can access all classes."""
        class1 = Class.objects.create(owner=user, name='Class 1')
        class2 = Class.objects.create(owner=another_user, name='Class 2')
        
        url = reverse('attendance:class-list')
        response = admin_authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
    
    def test_get_class_students(self, authenticated_client, user):
        """Test getting students in a class."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        Student.objects.create(class_enrolled=test_class, first_name='Alice', last_name='Smith')
        Student.objects.create(class_enrolled=test_class, first_name='Bob', last_name='Jones')
        
        url = reverse('attendance:class-students', kwargs={'pk': test_class.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
    
    def test_get_class_sessions(self, authenticated_client, user):
        """Test getting sessions in a class."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        Session.objects.create(class_session=test_class, name='Week 1', date=date.today())
        Session.objects.create(class_session=test_class, name='Week 2', date=date.today())
        
        url = reverse('attendance:class-sessions', kwargs={'pk': test_class.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
    
    def test_get_class_statistics(self, authenticated_client, user):
        """Test getting class statistics."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        Student.objects.create(class_enrolled=test_class, first_name='Alice', last_name='Smith')
        session = Session.objects.create(class_session=test_class, name='Week 1', date=date.today())
        
        url = reverse('attendance:class-statistics', kwargs={'pk': test_class.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'student_count' in response.data
        assert 'session_count' in response.data
        assert response.data['student_count'] == 1
        assert response.data['session_count'] == 1


@pytest.mark.django_db
class TestStudentAPI:
    """Test cases for Student API endpoints."""
    
    def test_list_students(self, authenticated_client, user):
        """Test listing students."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        Student.objects.create(class_enrolled=test_class, first_name='Alice', last_name='Smith')
        Student.objects.create(class_enrolled=test_class, first_name='Bob', last_name='Jones')
        
        url = reverse('attendance:student-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
    
    def test_filter_students_by_class(self, authenticated_client, user):
        """Test filtering students by class."""
        class1 = Class.objects.create(owner=user, name='CS 101')
        class2 = Class.objects.create(owner=user, name='Math 101')
        Student.objects.create(class_enrolled=class1, first_name='Alice', last_name='Smith')
        Student.objects.create(class_enrolled=class2, first_name='Bob', last_name='Jones')
        
        url = reverse('attendance:student-list')
        response = authenticated_client.get(url, {'class_id': class1.id})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['first_name'] == 'Alice'
    
    def test_create_student(self, authenticated_client, user):
        """Test creating a student."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        
        url = reverse('attendance:student-list')
        data = {
            'class_enrolled': test_class.id,
            'first_name': 'Charlie',
            'last_name': 'Brown',
            'student_id': 'S001',
            'email': 'charlie@example.com'
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['first_name'] == 'Charlie'
        assert response.data['last_name'] == 'Brown'
        assert response.data['full_name'] == 'Charlie Brown'
    
    def test_cannot_create_student_in_other_user_class(self, authenticated_client, another_user):
        """Test that users cannot create students in other users' classes."""
        other_class = Class.objects.create(owner=another_user, name='Other Class')
        
        url = reverse('attendance:student-list')
        data = {
            'class_enrolled': other_class.id,
            'first_name': 'Charlie',
            'last_name': 'Brown'
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_update_student(self, authenticated_client, user):
        """Test updating a student."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        student = Student.objects.create(
            class_enrolled=test_class,
            first_name='Alice',
            last_name='Smith'
        )
        
        url = reverse('attendance:student-detail', kwargs={'pk': student.pk})
        data = {
            'class_enrolled': test_class.id,
            'first_name': 'Alice',
            'last_name': 'Johnson',
            'student_id': 'S002',
            'email': 'alice.j@example.com'
        }
        response = authenticated_client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['last_name'] == 'Johnson'
        assert response.data['student_id'] == 'S002'
    
    def test_delete_student(self, authenticated_client, user):
        """Test deleting a student."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        student = Student.objects.create(
            class_enrolled=test_class,
            first_name='Alice',
            last_name='Smith'
        )
        
        url = reverse('attendance:student-detail', kwargs={'pk': student.pk})
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Student.objects.filter(pk=student.pk).exists()
    
    def test_get_student_attendance(self, authenticated_client, user):
        """Test getting student attendance statistics."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        student = Student.objects.create(
            class_enrolled=test_class,
            first_name='Alice',
            last_name='Smith'
        )
        session = Session.objects.create(
            class_session=test_class,
            name='Week 1',
            date=date.today()
        )
        
        url = reverse('attendance:student-attendance', kwargs={'pk': student.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'total_sessions' in response.data
        assert 'attended_sessions' in response.data
        assert 'attendance_rate' in response.data


@pytest.mark.django_db
class TestSessionAPI:
    """Test cases for Session API endpoints."""
    
    def test_list_sessions(self, authenticated_client, user):
        """Test listing sessions."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        Session.objects.create(class_session=test_class, name='Week 1', date=date.today())
        Session.objects.create(class_session=test_class, name='Week 2', date=date.today())
        
        url = reverse('attendance:session-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
    
    def test_filter_sessions_by_class(self, authenticated_client, user):
        """Test filtering sessions by class."""
        class1 = Class.objects.create(owner=user, name='CS 101')
        class2 = Class.objects.create(owner=user, name='Math 101')
        Session.objects.create(class_session=class1, name='CS Week 1', date=date.today())
        Session.objects.create(class_session=class2, name='Math Week 1', date=date.today())
        
        url = reverse('attendance:session-list')
        response = authenticated_client.get(url, {'class_id': class1.id})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'CS Week 1'
    
    def test_create_session(self, authenticated_client, user):
        """Test creating a session."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        
        url = reverse('attendance:session-list')
        data = {
            'class_session': test_class.id,
            'name': 'Week 3',
            'date': '2025-10-30',
            'start_time': '10:00:00',
            'end_time': '11:30:00',
            'notes': 'Test lecture'
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Week 3'
        assert response.data['notes'] == 'Test lecture'
    
    def test_update_session(self, authenticated_client, user):
        """Test updating a session."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        session = Session.objects.create(
            class_session=test_class,
            name='Week 1',
            date=date.today()
        )
        
        url = reverse('attendance:session-detail', kwargs={'pk': session.pk})
        data = {
            'class_session': test_class.id,
            'name': 'Week 1 Updated',
            'date': str(date.today()),
            'notes': 'Updated notes'
        }
        response = authenticated_client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Week 1 Updated'
        assert response.data['notes'] == 'Updated notes'
    
    def test_delete_session(self, authenticated_client, user):
        """Test deleting a session."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        session = Session.objects.create(
            class_session=test_class,
            name='Week 1',
            date=date.today()
        )
        
        url = reverse('attendance:session-detail', kwargs={'pk': session.pk})
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Session.objects.filter(pk=session.pk).exists()
    
    def test_get_session_images(self, authenticated_client, user):
        """Test getting images in a session."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        session = Session.objects.create(
            class_session=test_class,
            name='Week 1',
            date=date.today()
        )
        Image.objects.create(session=session, original_image_path='/path/img1.jpg')
        Image.objects.create(session=session, original_image_path='/path/img2.jpg')
        
        url = reverse('attendance:session-images', kwargs={'pk': session.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
    
    def test_get_session_attendance(self, authenticated_client, user):
        """Test getting attendance report for a session."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        alice = Student.objects.create(class_enrolled=test_class, first_name='Alice', last_name='Smith')
        bob = Student.objects.create(class_enrolled=test_class, first_name='Bob', last_name='Jones')
        
        session = Session.objects.create(
            class_session=test_class,
            name='Week 1',
            date=date.today()
        )
        image = Image.objects.create(session=session, original_image_path='/path/img1.jpg')
        crop = FaceCrop.objects.create(
            image=image,
            crop_image_path='/path/crop1.jpg',
            coordinates='0,0,100,100'
        )
        crop.identify_student(alice)
        
        url = reverse('attendance:session-attendance', kwargs={'pk': session.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_students'] == 2
        assert response.data['present_count'] == 1
        assert response.data['absent_count'] == 1


@pytest.mark.django_db
class TestImageAPI:
    """Test cases for Image API endpoints."""
    
    def test_list_images(self, authenticated_client, user):
        """Test listing images."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        session = Session.objects.create(class_session=test_class, name='Week 1', date=date.today())
        Image.objects.create(session=session, original_image_path='/path/img1.jpg')
        Image.objects.create(session=session, original_image_path='/path/img2.jpg')
        
        url = reverse('attendance:image-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
    
    def test_filter_images_by_session(self, authenticated_client, user):
        """Test filtering images by session."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        session1 = Session.objects.create(class_session=test_class, name='Week 1', date=date.today())
        session2 = Session.objects.create(class_session=test_class, name='Week 2', date=date.today())
        Image.objects.create(session=session1, original_image_path='/path/img1.jpg')
        Image.objects.create(session=session2, original_image_path='/path/img2.jpg')
        
        url = reverse('attendance:image-list')
        response = authenticated_client.get(url, {'session_id': session1.id})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
    
    def test_create_image(self, authenticated_client, user):
        """Test creating an image."""
        from io import BytesIO
        from PIL import Image as PILImage
        
        test_class = Class.objects.create(owner=user, name='CS 101')
        session = Session.objects.create(class_session=test_class, name='Week 1', date=date.today())
        
        # Create a temporary image file
        image_file = BytesIO()
        pil_image = PILImage.new('RGB', (100, 100), color='red')
        pil_image.save(image_file, 'JPEG')
        image_file.seek(0)
        image_file.name = 'test_image.jpg'
        
        url = reverse('attendance:image-list')
        data = {
            'session': session.id,
            'original_image_path': image_file
        }
        response = authenticated_client.post(url, data, format='multipart')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'test_image' in response.data['original_image_path']
        assert response.data['is_processed'] is False
    
    def test_delete_image(self, authenticated_client, user):
        """Test deleting an image."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        session = Session.objects.create(class_session=test_class, name='Week 1', date=date.today())
        image = Image.objects.create(session=session, original_image_path='/path/img1.jpg')
        
        url = reverse('attendance:image-detail', kwargs={'pk': image.pk})
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Image.objects.filter(pk=image.pk).exists()
    
    def test_mark_image_as_processed(self, authenticated_client, user):
        """Test marking an image as processed."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        session = Session.objects.create(class_session=test_class, name='Week 1', date=date.today())
        image = Image.objects.create(session=session, original_image_path='/path/img1.jpg')
        
        url = reverse('attendance:image-mark-processed', kwargs={'pk': image.pk})
        data = {'processed_image_path': '/processed/img1.jpg'}
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_processed'] is True
        # ImageField returns full URL including domain, not just the path
        assert '/processed/img1.jpg' in response.data['processed_image_path']
    
    def test_get_image_face_crops(self, authenticated_client, user):
        """Test getting face crops for an image."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        session = Session.objects.create(class_session=test_class, name='Week 1', date=date.today())
        image = Image.objects.create(session=session, original_image_path='/path/img1.jpg')
        FaceCrop.objects.create(image=image, crop_image_path='/crop1.jpg', coordinates='0,0,100,100')
        FaceCrop.objects.create(image=image, crop_image_path='/crop2.jpg', coordinates='100,0,100,100')
        
        url = reverse('attendance:image-face-crops', kwargs={'pk': image.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2


@pytest.mark.django_db
class TestFaceCropAPI:
    """Test cases for FaceCrop API endpoints."""
    
    def test_list_face_crops(self, authenticated_client, user):
        """Test listing face crops."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        session = Session.objects.create(class_session=test_class, name='Week 1', date=date.today())
        image = Image.objects.create(session=session, original_image_path='/path/img1.jpg')
        FaceCrop.objects.create(image=image, crop_image_path='/crop1.jpg', coordinates='0,0,100,100')
        FaceCrop.objects.create(image=image, crop_image_path='/crop2.jpg', coordinates='100,0,100,100')
        
        url = reverse('attendance:facecrop-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
    
    def test_update_face_crop_student(self, authenticated_client, user):
        """Test updating the student field of a face crop."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        student = Student.objects.create(class_enrolled=test_class, first_name='Alice', last_name='Smith')
        session = Session.objects.create(class_session=test_class, name='Week 1', date=date.today())
        image = Image.objects.create(session=session, original_image_path='/path/img1.jpg')
        crop = FaceCrop.objects.create(image=image, crop_image_path='/crop1.jpg', coordinates='0,0,100,100')
        
        url = reverse('attendance:facecrop-detail', kwargs={'pk': crop.pk})
        data = {'student': student.id}
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['student'] == student.id
        assert response.data['is_identified'] is True
    
    def test_cannot_assign_student_from_different_class(self, authenticated_client, user):
        """Test that you cannot assign a student from a different class."""
        class1 = Class.objects.create(owner=user, name='CS 101')
        class2 = Class.objects.create(owner=user, name='Math 101')
        student = Student.objects.create(class_enrolled=class2, first_name='Alice', last_name='Smith')
        session = Session.objects.create(class_session=class1, name='Week 1', date=date.today())
        image = Image.objects.create(session=session, original_image_path='/path/img1.jpg')
        crop = FaceCrop.objects.create(image=image, crop_image_path='/crop1.jpg', coordinates='0,0,100,100')
        
        url = reverse('attendance:facecrop-detail', kwargs={'pk': crop.pk})
        data = {'student': student.id}
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_unidentify_face_crop(self, authenticated_client, user):
        """Test clearing the student assignment from a face crop."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        student = Student.objects.create(class_enrolled=test_class, first_name='Alice', last_name='Smith')
        session = Session.objects.create(class_session=test_class, name='Week 1', date=date.today())
        image = Image.objects.create(session=session, original_image_path='/path/img1.jpg')
        crop = FaceCrop.objects.create(image=image, crop_image_path='/crop1.jpg', coordinates='0,0,100,100')
        crop.identify_student(student)
        
        url = reverse('attendance:facecrop-unidentify', kwargs={'pk': crop.pk})
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['student'] is None
        assert response.data['is_identified'] is False
    
    def test_filter_face_crops_by_identified(self, authenticated_client, user):
        """Test filtering face crops by identification status."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        student = Student.objects.create(class_enrolled=test_class, first_name='Alice', last_name='Smith')
        session = Session.objects.create(class_session=test_class, name='Week 1', date=date.today())
        image = Image.objects.create(session=session, original_image_path='/path/img1.jpg')
        
        crop1 = FaceCrop.objects.create(image=image, crop_image_path='/crop1.jpg', coordinates='0,0,100,100')
        crop1.identify_student(student)
        crop2 = FaceCrop.objects.create(image=image, crop_image_path='/crop2.jpg', coordinates='100,0,100,100')
        
        # Filter for identified
        url = reverse('attendance:facecrop-list')
        response = authenticated_client.get(url, {'is_identified': 'true'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        
        # Filter for unidentified
        response = authenticated_client.get(url, {'is_identified': 'false'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1


@pytest.mark.django_db
class TestPermissions:
    """Test permission checks across all endpoints."""
    
    def test_user_cannot_access_other_user_resources(self, authenticated_client, another_user):
        """Test that users cannot access resources belonging to other users."""
        # Create resources owned by another user
        other_class = Class.objects.create(owner=another_user, name='Other Class')
        other_student = Student.objects.create(
            class_enrolled=other_class,
            first_name='Other',
            last_name='Student'
        )
        other_session = Session.objects.create(
            class_session=other_class,
            name='Other Session',
            date=date.today()
        )
        other_image = Image.objects.create(
            session=other_session,
            original_image_path='/other/img.jpg'
        )
        other_crop = FaceCrop.objects.create(
            image=other_image,
            crop_image_path='/other/crop.jpg',
            coordinates='0,0,100,100'
        )
        
        # Try to access these resources
        assert authenticated_client.get(
            reverse('attendance:class-detail', kwargs={'pk': other_class.pk})
        ).status_code == status.HTTP_404_NOT_FOUND
        
        assert authenticated_client.get(
            reverse('attendance:student-detail', kwargs={'pk': other_student.pk})
        ).status_code == status.HTTP_404_NOT_FOUND
        
        assert authenticated_client.get(
            reverse('attendance:session-detail', kwargs={'pk': other_session.pk})
        ).status_code == status.HTTP_404_NOT_FOUND
        
        assert authenticated_client.get(
            reverse('attendance:image-detail', kwargs={'pk': other_image.pk})
        ).status_code == status.HTTP_404_NOT_FOUND
        
        assert authenticated_client.get(
            reverse('attendance:facecrop-detail', kwargs={'pk': other_crop.pk})
        ).status_code == status.HTTP_404_NOT_FOUND
    
    def test_admin_can_access_all_resources(self, admin_authenticated_client, user):
        """Test that admin users can access all resources."""
        # Create resources owned by a regular user
        user_class = Class.objects.create(owner=user, name='User Class')
        user_student = Student.objects.create(
            class_enrolled=user_class,
            first_name='User',
            last_name='Student'
        )
        user_session = Session.objects.create(
            class_session=user_class,
            name='User Session',
            date=date.today()
        )
        user_image = Image.objects.create(
            session=user_session,
            original_image_path='/user/img.jpg'
        )
        user_crop = FaceCrop.objects.create(
            image=user_image,
            crop_image_path='/user/crop.jpg',
            coordinates='0,0,100,100'
        )
        
        # Admin should be able to access all resources
        assert admin_authenticated_client.get(
            reverse('attendance:class-detail', kwargs={'pk': user_class.pk})
        ).status_code == status.HTTP_200_OK
        
        assert admin_authenticated_client.get(
            reverse('attendance:student-detail', kwargs={'pk': user_student.pk})
        ).status_code == status.HTTP_200_OK
        
        assert admin_authenticated_client.get(
            reverse('attendance:session-detail', kwargs={'pk': user_session.pk})
        ).status_code == status.HTTP_200_OK
        
        assert admin_authenticated_client.get(
            reverse('attendance:image-detail', kwargs={'pk': user_image.pk})
        ).status_code == status.HTTP_200_OK
        
        assert admin_authenticated_client.get(
            reverse('attendance:facecrop-detail', kwargs={'pk': user_crop.pk})
        ).status_code == status.HTTP_200_OK
