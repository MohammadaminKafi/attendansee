import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from datetime import date, time, datetime
from attendance.models import Class, Student, Session, Image, FaceCrop


User = get_user_model()


@pytest.mark.django_db
class TestStudentDetailReport:
    """Test cases for student detail report endpoint."""
    
    def test_get_student_detail_report(self, authenticated_client, user):
        """Test retrieving student detail report."""
        # Create test data
        test_class = Class.objects.create(owner=user, name='CS 101')
        student = Student.objects.create(
            class_enrolled=test_class,
            first_name='John',
            last_name='Doe',
            student_id='12345'
        )
        
        # Create sessions
        session1 = Session.objects.create(
            class_session=test_class,
            name='Session 1',
            date=date.today()
        )
        session2 = Session.objects.create(
            class_session=test_class,
            name='Session 2',
            date=date.today()
        )
        
        # Create images and face crops for session 1
        image1 = Image.objects.create(
            session=session1,
            original_image_path='/media/test1.jpg',
            is_processed=True
        )
        crop1 = FaceCrop.objects.create(
            image=image1,
            student=student,
            crop_image_path='/media/crop1.jpg',
            coordinates='10,20,100,100',
            is_identified=True
        )
        
        # Call endpoint
        url = reverse('attendance:student-detail-report', kwargs={'pk': student.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'student' in response.data
        assert 'statistics' in response.data
        assert 'sessions' in response.data
        
        # Check student info
        assert response.data['student']['id'] == student.id
        assert response.data['student']['first_name'] == 'John'
        
        # Check statistics
        stats = response.data['statistics']
        assert stats['total_sessions'] == 2
        assert stats['attended_sessions'] == 1
        assert stats['missed_sessions'] == 1
        assert stats['total_detections'] == 1
        
        # Check sessions
        sessions = response.data['sessions']
        assert len(sessions) == 2
        
        # Check session with attendance
        attended_session = next(s for s in sessions if s['session_id'] == session1.id)
        assert attended_session['was_present'] is True
        assert attended_session['detection_count'] == 1
        assert len(attended_session['face_crops']) == 1
        
        # Check session without attendance
        absent_session = next(s for s in sessions if s['session_id'] == session2.id)
        assert absent_session['was_present'] is False
        assert absent_session['detection_count'] == 0
        assert len(absent_session['face_crops']) == 0
    
    def test_student_detail_report_no_attendance(self, authenticated_client, user):
        """Test detail report for student with no attendance."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        student = Student.objects.create(
            class_enrolled=test_class,
            first_name='Jane',
            last_name='Smith',
            student_id='54321'
        )
        
        # Create session without any attendance
        Session.objects.create(
            class_session=test_class,
            name='Session 1',
            date=date.today()
        )
        
        url = reverse('attendance:student-detail-report', kwargs={'pk': student.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        stats = response.data['statistics']
        assert stats['total_sessions'] == 1
        assert stats['attended_sessions'] == 0
        assert stats['attendance_rate'] == 0.0
    
    def test_cannot_access_other_user_student_report(self, authenticated_client, another_user):
        """Test that users cannot access reports for students in other users' classes."""
        # Create class and student for another user
        other_class = Class.objects.create(owner=another_user, name='Other Class')
        other_student = Student.objects.create(
            class_enrolled=other_class,
            first_name='Other',
            last_name='Student',
            student_id='99999'
        )
        
        url = reverse('attendance:student-detail-report', kwargs={'pk': other_student.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestAttendanceReport:
    """Test cases for class attendance report endpoint."""
    
    def test_get_attendance_report(self, authenticated_client, user):
        """Test retrieving attendance report for a class."""
        # Create test data
        test_class = Class.objects.create(owner=user, name='CS 101')
        
        # Create students
        student1 = Student.objects.create(
            class_enrolled=test_class,
            first_name='John',
            last_name='Doe',
            student_id='12345'
        )
        student2 = Student.objects.create(
            class_enrolled=test_class,
            first_name='Jane',
            last_name='Smith',
            student_id='54321'
        )
        
        # Create sessions
        session1 = Session.objects.create(
            class_session=test_class,
            name='Session 1',
            date=date.today(),
            is_processed=True
        )
        session2 = Session.objects.create(
            class_session=test_class,
            name='Session 2',
            date=date.today(),
            is_processed=True
        )
        
        # Create attendance - student1 attends both, student2 attends only session1
        image1 = Image.objects.create(
            session=session1,
            original_image_path='/media/test1.jpg',
            is_processed=True
        )
        image2 = Image.objects.create(
            session=session2,
            original_image_path='/media/test2.jpg',
            is_processed=True
        )
        
        # Student 1 in both sessions
        FaceCrop.objects.create(
            image=image1,
            student=student1,
            crop_image_path='/media/crop1.jpg',
            coordinates='10,20,100,100',
            is_identified=True
        )
        FaceCrop.objects.create(
            image=image2,
            student=student1,
            crop_image_path='/media/crop2.jpg',
            coordinates='10,20,100,100',
            is_identified=True
        )
        
        # Student 2 only in session 1
        FaceCrop.objects.create(
            image=image1,
            student=student2,
            crop_image_path='/media/crop3.jpg',
            coordinates='10,20,100,100',
            is_identified=True
        )
        
        # Call endpoint
        url = reverse('attendance:class-attendance-report', kwargs={'pk': test_class.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'class_id' in response.data
        assert 'sessions' in response.data
        assert 'attendance_matrix' in response.data
        
        # Check class info
        assert response.data['class_id'] == test_class.id
        assert response.data['class_name'] == 'CS 101'
        assert response.data['total_students'] == 2
        assert response.data['total_sessions'] == 2
        
        # Check sessions
        sessions = response.data['sessions']
        assert len(sessions) == 2
        assert sessions[0]['present_count'] == 2  # Both students in session 1
        assert sessions[1]['present_count'] == 1  # Only student1 in session 2
        
        # Check attendance matrix
        matrix = response.data['attendance_matrix']
        assert len(matrix) == 2
        
        # Check student 1 (100% attendance)
        student1_data = next(s for s in matrix if s['student_id'] == student1.id)
        assert student1_data['attended_sessions'] == 2
        assert student1_data['attendance_rate'] == 100.0
        assert len(student1_data['session_attendance']) == 2
        assert all(a['present'] for a in student1_data['session_attendance'])
        
        # Check student 2 (50% attendance)
        student2_data = next(s for s in matrix if s['student_id'] == student2.id)
        assert student2_data['attended_sessions'] == 1
        assert student2_data['attendance_rate'] == 50.0
        assert student2_data['session_attendance'][0]['present'] is True
        assert student2_data['session_attendance'][1]['present'] is False
    
    def test_attendance_report_empty_class(self, authenticated_client, user):
        """Test attendance report for class with no students or sessions."""
        test_class = Class.objects.create(owner=user, name='Empty Class')
        
        url = reverse('attendance:class-attendance-report', kwargs={'pk': test_class.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_students'] == 0
        assert response.data['total_sessions'] == 0
        assert len(response.data['attendance_matrix']) == 0
    
    def test_attendance_report_filter_by_date(self, authenticated_client, user):
        """Test filtering attendance report by date range."""
        from datetime import timedelta
        
        test_class = Class.objects.create(owner=user, name='CS 101')
        student = Student.objects.create(
            class_enrolled=test_class,
            first_name='John',
            last_name='Doe',
            student_id='12345'
        )
        
        # Create sessions on different dates
        today = date.today()
        session1 = Session.objects.create(
            class_session=test_class,
            name='Old Session',
            date=today - timedelta(days=10),
            is_processed=True
        )
        session2 = Session.objects.create(
            class_session=test_class,
            name='Recent Session',
            date=today,
            is_processed=True
        )
        
        # Filter to only recent session
        url = reverse('attendance:class-attendance-report', kwargs={'pk': test_class.pk})
        response = authenticated_client.get(
            url,
            {'date_from': (today - timedelta(days=1)).strftime('%Y-%m-%d')}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_sessions'] == 1
        assert response.data['sessions'][0]['id'] == session2.id
    
    def test_attendance_report_include_unprocessed(self, authenticated_client, user):
        """Test including unprocessed sessions in report."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        
        # Create processed and unprocessed sessions
        Session.objects.create(
            class_session=test_class,
            name='Processed',
            date=date.today(),
            is_processed=True
        )
        Session.objects.create(
            class_session=test_class,
            name='Unprocessed',
            date=date.today(),
            is_processed=False
        )
        
        # Default: exclude unprocessed
        url = reverse('attendance:class-attendance-report', kwargs={'pk': test_class.pk})
        response = authenticated_client.get(url)
        assert response.data['total_sessions'] == 1
        
        # Include unprocessed
        response = authenticated_client.get(url, {'include_unprocessed': 'true'})
        assert response.data['total_sessions'] == 2
    
    def test_cannot_access_other_user_attendance_report(self, authenticated_client, another_user):
        """Test that users cannot access reports for other users' classes."""
        other_class = Class.objects.create(owner=another_user, name='Other Class')
        
        url = reverse('attendance:class-attendance-report', kwargs={'pk': other_class.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestStudentListPagination:
    """Test cases for student list pagination."""
    
    def test_student_list_default_pagination(self, authenticated_client, user):
        """Test default pagination (20 items per page)."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        
        # Create 25 students
        for i in range(25):
            Student.objects.create(
                class_enrolled=test_class,
                first_name=f'Student',
                last_name=f'{i}',
                student_id=f'{i:05d}'
            )
        
        url = reverse('attendance:student-list')
        response = authenticated_client.get(url, {'class_id': test_class.id})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 20
        assert response.data['count'] == 25
        assert response.data['next'] is not None
    
    def test_student_list_custom_page_size(self, authenticated_client, user):
        """Test custom page_size parameter."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        
        # Create 50 students
        for i in range(50):
            Student.objects.create(
                class_enrolled=test_class,
                first_name=f'Student',
                last_name=f'{i}',
                student_id=f'{i:05d}'
            )
        
        url = reverse('attendance:student-list')
        response = authenticated_client.get(
            url,
            {'class_id': test_class.id, 'page_size': 100}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 50
        assert response.data['count'] == 50
        assert response.data['next'] is None
    
    def test_student_list_page_size_limit(self, authenticated_client, user):
        """Test that page_size is limited to max 10000."""
        test_class = Class.objects.create(owner=user, name='CS 101')
        
        # Create 10 students
        for i in range(10):
            Student.objects.create(
                class_enrolled=test_class,
                first_name=f'Student',
                last_name=f'{i}',
                student_id=f'{i:05d}'
            )
        
        # Request with very large page_size
        url = reverse('attendance:student-list')
        response = authenticated_client.get(
            url,
            {'class_id': test_class.id, 'page_size': 999999}
        )
        
        # Should still work and return all students
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 10
