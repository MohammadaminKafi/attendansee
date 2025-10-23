import pytest
import io
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from attendance.models import Class, Student, Session, Image, FaceCrop


User = get_user_model()


@pytest.mark.django_db
class TestBulkStudentUpload:
    """Test cases for bulk student upload from CSV/Excel."""
    
    def test_bulk_upload_csv_with_header(self, authenticated_client, test_class):
        """Test bulk upload of students from CSV file with header."""
        # Create CSV content
        csv_content = """first_name,last_name,student_id
John,Doe,S001
Jane,Smith,S002
Bob,Johnson,S003
"""
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = 'students.csv'
        
        url = reverse('attendance:class-bulk-upload-students', kwargs={'pk': test_class.pk})
        response = authenticated_client.post(
            url,
            {'file': csv_file, 'has_header': True},
            format='multipart'
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['total_created'] == 3
        assert response.data['total_skipped'] == 0
        assert len(response.data['created']) == 3
        
        # Verify students were created in database
        assert Student.objects.filter(class_enrolled=test_class).count() == 3
        assert Student.objects.filter(
            class_enrolled=test_class,
            first_name='John',
            last_name='Doe',
            student_id='S001'
        ).exists()
    
    def test_bulk_upload_csv_without_header(self, authenticated_client, test_class):
        """Test bulk upload from CSV file without header."""
        csv_content = """Alice,Brown,S101
Charlie,Davis,S102
"""
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = 'students.csv'
        
        url = reverse('attendance:class-bulk-upload-students', kwargs={'pk': test_class.pk})
        response = authenticated_client.post(
            url,
            {'file': csv_file, 'has_header': False},
            format='multipart'
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['total_created'] == 2
        assert Student.objects.filter(
            class_enrolled=test_class,
            first_name='Alice',
            last_name='Brown'
        ).exists()
    
    def test_bulk_upload_csv_without_student_id(self, authenticated_client, test_class):
        """Test bulk upload with only first_name and last_name."""
        csv_content = """first_name,last_name
Emma,Wilson
Oliver,Taylor
"""
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = 'students.csv'
        
        url = reverse('attendance:class-bulk-upload-students', kwargs={'pk': test_class.pk})
        response = authenticated_client.post(
            url,
            {'file': csv_file, 'has_header': True},
            format='multipart'
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['total_created'] == 2
        
        # Verify students were created with empty student_id
        emma = Student.objects.get(
            class_enrolled=test_class,
            first_name='Emma',
            last_name='Wilson'
        )
        assert emma.student_id == ''
    
    def test_bulk_upload_skip_duplicates(self, authenticated_client, test_class, student1):
        """Test that duplicate students are skipped."""
        # student1 fixture creates Alice Johnson in test_class
        csv_content = f"""first_name,last_name,student_id
{student1.first_name},{student1.last_name},S999
Bob,Williams,S002
"""
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = 'students.csv'
        
        url = reverse('attendance:class-bulk-upload-students', kwargs={'pk': test_class.pk})
        response = authenticated_client.post(
            url,
            {'file': csv_file, 'has_header': True},
            format='multipart'
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['total_created'] == 1
        assert response.data['total_skipped'] == 1
        assert len(response.data['skipped']) == 1
        assert response.data['skipped'][0]['reason'] == 'Already exists'
    
    def test_bulk_upload_empty_file(self, authenticated_client, test_class):
        """Test upload with empty file."""
        csv_file = io.BytesIO(b'')
        csv_file.name = 'empty.csv'
        
        url = reverse('attendance:class-bulk-upload-students', kwargs={'pk': test_class.pk})
        response = authenticated_client.post(
            url,
            {'file': csv_file},
            format='multipart'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'file' in response.data
    
    def test_bulk_upload_invalid_extension(self, authenticated_client, test_class):
        """Test upload with invalid file extension."""
        txt_file = io.BytesIO(b'Some text')
        txt_file.name = 'students.txt'
        
        url = reverse('attendance:class-bulk-upload-students', kwargs={'pk': test_class.pk})
        response = authenticated_client.post(
            url,
            {'file': txt_file},
            format='multipart'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'file' in response.data
    
    def test_bulk_upload_large_file(self, authenticated_client, test_class):
        """Test upload with file exceeding size limit."""
        # Create a file larger than 5MB
        large_content = 'first_name,last_name,student_id\n' + ('a,b,c\n' * 1000000)
        large_file = io.BytesIO(large_content.encode('utf-8'))
        large_file.name = 'large.csv'
        
        url = reverse('attendance:class-bulk-upload-students', kwargs={'pk': test_class.pk})
        response = authenticated_client.post(
            url,
            {'file': large_file},
            format='multipart'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_bulk_upload_missing_required_columns(self, authenticated_client, test_class):
        """Test upload with missing required columns."""
        csv_content = """first_name
John
Jane
"""
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = 'students.csv'
        
        url = reverse('attendance:class-bulk-upload-students', kwargs={'pk': test_class.pk})
        response = authenticated_client.post(
            url,
            {'file': csv_file, 'has_header': True},
            format='multipart'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_bulk_upload_empty_names(self, authenticated_client, test_class):
        """Test upload with empty first_name or last_name."""
        csv_content = """first_name,last_name,student_id
,Doe,S001
Jane,,S002
"""
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = 'students.csv'
        
        url = reverse('attendance:class-bulk-upload-students', kwargs={'pk': test_class.pk})
        response = authenticated_client.post(
            url,
            {'file': csv_file, 'has_header': True},
            format='multipart'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_bulk_upload_skip_empty_rows(self, authenticated_client, test_class):
        """Test that empty rows are skipped."""
        csv_content = """first_name,last_name,student_id
John,Doe,S001

Jane,Smith,S002
,,
Bob,Johnson,S003
"""
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = 'students.csv'
        
        url = reverse('attendance:class-bulk-upload-students', kwargs={'pk': test_class.pk})
        response = authenticated_client.post(
            url,
            {'file': csv_file, 'has_header': True},
            format='multipart'
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['total_created'] == 3
    
    def test_bulk_upload_unauthorized(self, api_client, test_class):
        """Test that unauthenticated users cannot upload."""
        csv_content = """first_name,last_name
John,Doe
"""
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = 'students.csv'
        
        url = reverse('attendance:class-bulk-upload-students', kwargs={'pk': test_class.pk})
        response = api_client.post(
            url,
            {'file': csv_file},
            format='multipart'
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_bulk_upload_wrong_class_owner(self, another_authenticated_client, test_class):
        """Test that users cannot upload to other users' classes."""
        csv_content = """first_name,last_name
John,Doe
"""
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = 'students.csv'
        
        url = reverse('attendance:class-bulk-upload-students', kwargs={'pk': test_class.pk})
        response = another_authenticated_client.post(
            url,
            {'file': csv_file},
            format='multipart'
        )
        
        # DRF returns 404 when object is filtered out by get_queryset()
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_bulk_upload_utf8_with_bom(self, authenticated_client, test_class):
        """Test CSV file with UTF-8 BOM."""
        csv_content = '\ufeff' + """first_name,last_name,student_id
José,García,S001
François,Dupont,S002
"""
        csv_file = io.BytesIO(csv_content.encode('utf-8-sig'))
        csv_file.name = 'students.csv'
        
        url = reverse('attendance:class-bulk-upload-students', kwargs={'pk': test_class.pk})
        response = authenticated_client.post(
            url,
            {'file': csv_file, 'has_header': True},
            format='multipart'
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['total_created'] == 2


@pytest.mark.django_db
class TestProcessImage:
    """Test cases for image processing endpoint."""
    
    def test_process_image_success(self, authenticated_client, image1):
        """Test processing an unprocessed image."""
        url = reverse('attendance:image-process-image', kwargs={'pk': image1.pk})
        response = authenticated_client.post(url, {}, format='json')
        
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data['status'] == 'processing_queued'
        assert response.data['image_id'] == image1.id
        assert response.data['session_id'] == image1.session.id
        assert 'faces_detected' in response.data
    
    def test_process_image_with_parameters(self, authenticated_client, image1):
        """Test processing with custom parameters."""
        url = reverse('attendance:image-process-image', kwargs={'pk': image1.pk})
        data = {
            'min_face_size': 30,
            'confidence_threshold': 0.8
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data['parameters']['min_face_size'] == 30
        assert response.data['parameters']['confidence_threshold'] == 0.8
    
    def test_process_image_already_processed(self, authenticated_client, processed_image):
        """Test processing an already processed image."""
        url = reverse('attendance:image-process-image', kwargs={'pk': processed_image.pk})
        response = authenticated_client.post(url, {}, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'already been processed' in response.data['error']
    
    def test_process_image_invalid_parameters(self, authenticated_client, image1):
        """Test processing with invalid parameters."""
        url = reverse('attendance:image-process-image', kwargs={'pk': image1.pk})
        data = {
            'min_face_size': -10,  # Invalid: negative value
            'confidence_threshold': 1.5  # Invalid: > 1.0
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_process_image_unauthorized(self, api_client, image1):
        """Test that unauthenticated users cannot process images."""
        url = reverse('attendance:image-process-image', kwargs={'pk': image1.pk})
        response = api_client.post(url, {}, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_process_image_wrong_owner(self, another_authenticated_client, image1):
        """Test that users cannot process images from other users' classes."""
        url = reverse('attendance:image-process-image', kwargs={'pk': image1.pk})
        response = another_authenticated_client.post(url, {}, format='json')
        
        # DRF returns 404 when object is filtered out by get_queryset()
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestAggregateCrops:
    """Test cases for session crop aggregation endpoint."""
    
    def test_aggregate_crops_success(self, authenticated_client, session1, processed_image):
        """Test aggregating crops from a session with processed images."""
        # Create a face crop linked to the processed_image
        FaceCrop.objects.create(
            image=processed_image,
            crop_image_path='/path/to/crops/crop_test.jpg',
            coordinates='100,150,200,250',
            is_identified=False
        )
        
        url = reverse('attendance:session-aggregate-crops', kwargs={'pk': session1.pk})
        response = authenticated_client.post(url, {}, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'aggregation_completed'
        assert response.data['session_id'] == session1.id
        assert 'statistics' in response.data
        assert 'total_crops' in response.data['statistics']
    
    def test_aggregate_crops_with_parameters(self, authenticated_client, session1, processed_image):
        """Test aggregation with custom parameters."""
        url = reverse('attendance:session-aggregate-crops', kwargs={'pk': session1.pk})
        data = {
            'similarity_threshold': 0.85,
            'auto_assign': True
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['parameters']['similarity_threshold'] == 0.85
        assert response.data['parameters']['auto_assign'] is True
    
    def test_aggregate_crops_no_images(self, authenticated_client, session2):
        """Test aggregation on session with no images."""
        url = reverse('attendance:session-aggregate-crops', kwargs={'pk': session2.pk})
        response = authenticated_client.post(url, {}, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'no images' in response.data['error'].lower()
    
    def test_aggregate_crops_unprocessed_images(self, authenticated_client, session1, image1, image2):
        """Test aggregation with unprocessed images."""
        # image1 and image2 are not processed
        url = reverse('attendance:session-aggregate-crops', kwargs={'pk': session1.pk})
        response = authenticated_client.post(url, {}, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'not yet processed' in response.data['warning']
    
    def test_aggregate_crops_invalid_threshold(self, authenticated_client, session1, processed_image):
        """Test aggregation with invalid similarity threshold."""
        url = reverse('attendance:session-aggregate-crops', kwargs={'pk': session1.pk})
        data = {
            'similarity_threshold': 1.5  # Invalid: > 1.0
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_aggregate_crops_unauthorized(self, api_client, session1):
        """Test that unauthenticated users cannot aggregate crops."""
        url = reverse('attendance:session-aggregate-crops', kwargs={'pk': session1.pk})
        response = api_client.post(url, {}, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_aggregate_crops_wrong_owner(self, another_authenticated_client, session1, processed_image):
        """Test that users cannot aggregate crops from other users' sessions."""
        url = reverse('attendance:session-aggregate-crops', kwargs={'pk': session1.pk})
        response = another_authenticated_client.post(url, {}, format='json')
        
        # DRF returns 404 when object is filtered out by get_queryset()
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestAggregateClass:
    """Test cases for class-level aggregation endpoint."""
    
    def test_aggregate_class_success(self, authenticated_client, test_class, session1, student1):
        """Test class-level aggregation."""
        url = reverse('attendance:class-aggregate-class', kwargs={'pk': test_class.pk})
        response = authenticated_client.post(url, {}, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['class_id'] == test_class.id
        assert response.data['class_name'] == test_class.name
        assert 'student_statistics' in response.data
        assert 'total_sessions' in response.data
    
    def test_aggregate_class_with_date_range(self, authenticated_client, test_class, session1, session2):
        """Test aggregation with date range filters."""
        url = reverse('attendance:class-aggregate-class', kwargs={'pk': test_class.pk})
        data = {
            'date_from': '2025-10-01',
            'date_to': '2025-10-20'
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'date_range' in response.data
    
    def test_aggregate_class_include_unprocessed(self, authenticated_client, test_class, session1):
        """Test aggregation including unprocessed sessions."""
        url = reverse('attendance:class-aggregate-class', kwargs={'pk': test_class.pk})
        data = {
            'include_unprocessed': True
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_aggregate_class_invalid_date_range(self, authenticated_client, test_class):
        """Test aggregation with invalid date range."""
        url = reverse('attendance:class-aggregate-class', kwargs={'pk': test_class.pk})
        data = {
            'date_from': '2025-10-20',
            'date_to': '2025-10-01'  # date_to before date_from
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_aggregate_class_no_sessions(self, authenticated_client, user):
        """Test aggregation on class with no sessions."""
        empty_class = Class.objects.create(
            owner=user,
            name='Empty Class'
        )
        
        url = reverse('attendance:class-aggregate-class', kwargs={'pk': empty_class.pk})
        response = authenticated_client.post(url, {}, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_sessions'] == 0
    
    def test_aggregate_class_unauthorized(self, api_client, test_class):
        """Test that unauthenticated users cannot aggregate class."""
        url = reverse('attendance:class-aggregate-class', kwargs={'pk': test_class.pk})
        response = api_client.post(url, {}, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_aggregate_class_wrong_owner(self, another_authenticated_client, test_class):
        """Test that users cannot aggregate other users' classes."""
        url = reverse('attendance:class-aggregate-class', kwargs={'pk': test_class.pk})
        response = another_authenticated_client.post(url, {}, format='json')
        
        # DRF returns 404 when object is filtered out by get_queryset()
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_aggregate_class_student_statistics(self, authenticated_client, test_class, session1, student1, student2, image1, face_crop1):
        """Test that student statistics are correctly calculated."""
        url = reverse('attendance:class-aggregate-class', kwargs={'pk': test_class.pk})
        response = authenticated_client.post(url, {}, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['student_statistics']) == 2  # student1 and student2
        
        # Find student1's stats
        student1_stats = next(
            (s for s in response.data['student_statistics'] if s['student_id'] == student1.id),
            None
        )
        assert student1_stats is not None
        assert 'attended_sessions' in student1_stats
        assert 'attendance_rate' in student1_stats
