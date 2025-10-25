import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from attendance.models import Class, Student, Session, Image, FaceCrop
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image as PILImage
import io


User = get_user_model()


def create_test_image():
    """Create a simple test image file."""
    image = PILImage.new('RGB', (100, 100), color='red')
    image_file = io.BytesIO()
    image.save(image_file, format='JPEG')
    image_file.seek(0)
    return SimpleUploadedFile(
        name='test_image.jpg',
        content=image_file.read(),
        content_type='image/jpeg'
    )


@pytest.mark.django_db
class TestMergeStudentsAPI:
    """Test cases for merging students."""
    
    @pytest.fixture
    def test_class(self, user):
        """Create a test class."""
        return Class.objects.create(owner=user, name='Test Class')
    
    @pytest.fixture
    def source_student(self, test_class):
        """Create a source student to merge from."""
        return Student.objects.create(
            class_enrolled=test_class,
            first_name='John',
            last_name='Doe',
            student_id='S001'
        )
    
    @pytest.fixture
    def target_student(self, test_class):
        """Create a target student to merge into."""
        return Student.objects.create(
            class_enrolled=test_class,
            first_name='Jane',
            last_name='Smith',
            student_id='S002'
        )
    
    @pytest.fixture
    def other_class_student(self, user):
        """Create a student in a different class."""
        other_class = Class.objects.create(owner=user, name='Other Class')
        return Student.objects.create(
            class_enrolled=other_class,
            first_name='Bob',
            last_name='Wilson',
            student_id='S003'
        )
    
    @pytest.fixture
    def session_with_crops(self, test_class, source_student):
        """Create a session with images and face crops for the source student."""
        session = Session.objects.create(
            class_session=test_class,
            name='Test Session',
            date='2024-01-01'
        )
        
        # Create an image
        image = Image.objects.create(
            session=session,
            original_image_path=create_test_image()
        )
        
        # Create face crops for the source student
        crops = []
        for i in range(3):
            crop = FaceCrop.objects.create(
                image=image,
                student=source_student,
                crop_image_path=create_test_image(),
                coordinates=f'10,20,{30+i*10},{40+i*10}',
                confidence_score=0.9,
                is_identified=True
            )
            crops.append(crop)
        
        return session, crops
    
    def test_successful_merge(self, authenticated_client, source_student, target_student, session_with_crops):
        """Test successful merge of two students."""
        session, crops = session_with_crops
        
        # Verify initial state
        assert source_student.face_crops.count() == 3
        assert target_student.face_crops.count() == 0
        
        url = reverse('attendance:student-merge', kwargs={'pk': source_student.pk})
        data = {'target_student_id': target_student.id}
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'success'
        assert response.data['statistics']['face_crops_transferred'] == 3
        assert response.data['statistics']['target_crops_before_merge'] == 0
        assert response.data['statistics']['target_crops_after_merge'] == 3
        
        # Verify source student is deleted
        assert not Student.objects.filter(id=source_student.id).exists()
        
        # Verify target student received all face crops
        target_student.refresh_from_db()
        assert target_student.face_crops.count() == 3
        
        # Verify face crops were correctly transferred
        for crop_id in [c.id for c in crops]:
            crop = FaceCrop.objects.get(id=crop_id)
            assert crop.student_id == target_student.id
    
    def test_merge_with_no_face_crops(self, authenticated_client, test_class):
        """Test merge when source student has no face crops."""
        source = Student.objects.create(
            class_enrolled=test_class,
            first_name='Empty',
            last_name='Student',
            student_id='S004'
        )
        target = Student.objects.create(
            class_enrolled=test_class,
            first_name='Target',
            last_name='Student',
            student_id='S005'
        )
        
        url = reverse('attendance:student-merge', kwargs={'pk': source.pk})
        data = {'target_student_id': target.id}
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['statistics']['face_crops_transferred'] == 0
        assert not Student.objects.filter(id=source.id).exists()
    
    def test_merge_student_with_itself(self, authenticated_client, source_student):
        """Test that merging a student with itself fails."""
        url = reverse('attendance:student-merge', kwargs={'pk': source_student.pk})
        data = {'target_student_id': source_student.id}
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Cannot merge a student with itself' in str(response.data)
    
    def test_merge_students_from_different_classes(
        self, authenticated_client, source_student, other_class_student
    ):
        """Test that merging students from different classes fails."""
        url = reverse('attendance:student-merge', kwargs={'pk': source_student.pk})
        data = {'target_student_id': other_class_student.id}
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'same class' in str(response.data).lower()
    
    def test_merge_with_nonexistent_target(self, authenticated_client, source_student):
        """Test merge with non-existent target student ID."""
        url = reverse('attendance:student-merge', kwargs={'pk': source_student.pk})
        data = {'target_student_id': 999999}
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'does not exist' in str(response.data).lower()
    
    def test_merge_without_target_id(self, authenticated_client, source_student):
        """Test merge without providing target_student_id."""
        url = reverse('attendance:student-merge', kwargs={'pk': source_student.pk})
        data = {}
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'target_student_id' in str(response.data).lower()
    
    def test_merge_unauthenticated(self, api_client, source_student, target_student):
        """Test that unauthenticated users cannot merge students."""
        url = reverse('attendance:student-merge', kwargs={'pk': source_student.pk})
        data = {'target_student_id': target_student.id}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_merge_other_users_students(
        self, authenticated_client, another_user
    ):
        """Test that users cannot merge students from classes they don't own."""
        # Create a class owned by another user
        other_class = Class.objects.create(owner=another_user, name='Other User Class')
        source = Student.objects.create(
            class_enrolled=other_class,
            first_name='Other',
            last_name='Source',
            student_id='S006'
        )
        target = Student.objects.create(
            class_enrolled=other_class,
            first_name='Other',
            last_name='Target',
            student_id='S007'
        )
        
        url = reverse('attendance:student-merge', kwargs={'pk': source.pk})
        data = {'target_student_id': target.id}
        
        response = authenticated_client.post(url, data, format='json')
        
        # Should return 404 because the user doesn't have access to this student
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_merge_preserves_face_crop_attributes(
        self, authenticated_client, source_student, target_student, session_with_crops
    ):
        """Test that face crop attributes are preserved during merge."""
        session, crops = session_with_crops
        
        # Store original crop data
        original_crops_data = [
            {
                'id': crop.id,
                'coordinates': crop.coordinates,
                'confidence_score': crop.confidence_score,
                'is_identified': crop.is_identified,
                'image_id': crop.image_id
            }
            for crop in crops
        ]
        
        url = reverse('attendance:student-merge', kwargs={'pk': source_student.pk})
        data = {'target_student_id': target_student.id}
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify all crop attributes are preserved except student_id
        for original_data in original_crops_data:
            crop = FaceCrop.objects.get(id=original_data['id'])
            assert crop.student_id == target_student.id
            assert crop.coordinates == original_data['coordinates']
            assert crop.confidence_score == original_data['confidence_score']
            assert crop.is_identified == original_data['is_identified']
            assert crop.image_id == original_data['image_id']
    
    def test_merge_with_both_students_having_crops(
        self, authenticated_client, source_student, target_student, test_class
    ):
        """Test merge when both students already have face crops."""
        # Create session with images
        session = Session.objects.create(
            class_session=test_class,
            name='Test Session',
            date='2024-01-01'
        )
        
        image = Image.objects.create(
            session=session,
            original_image_path=create_test_image()
        )
        
        # Create crops for source student
        for i in range(3):
            FaceCrop.objects.create(
                image=image,
                student=source_student,
                crop_image_path=create_test_image(),
                coordinates=f'10,20,{30+i*10},{40+i*10}',
                confidence_score=0.9,
                is_identified=True
            )
        
        # Create crops for target student
        for i in range(2):
            FaceCrop.objects.create(
                image=image,
                student=target_student,
                crop_image_path=create_test_image(),
                coordinates=f'50,60,{70+i*10},{80+i*10}',
                confidence_score=0.8,
                is_identified=True
            )
        
        assert source_student.face_crops.count() == 3
        assert target_student.face_crops.count() == 2
        
        url = reverse('attendance:student-merge', kwargs={'pk': source_student.pk})
        data = {'target_student_id': target_student.id}
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['statistics']['face_crops_transferred'] == 3
        assert response.data['statistics']['target_crops_before_merge'] == 2
        assert response.data['statistics']['target_crops_after_merge'] == 5
        
        # Verify target student has all crops
        target_student.refresh_from_db()
        assert target_student.face_crops.count() == 5
    
    def test_merge_response_includes_student_data(
        self, authenticated_client, source_student, target_student
    ):
        """Test that merge response includes proper student data."""
        url = reverse('attendance:student-merge', kwargs={'pk': source_student.pk})
        data = {'target_student_id': target_student.id}
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check source student info
        assert response.data['source_student']['id'] == source_student.id
        assert response.data['source_student']['full_name'] == source_student.full_name
        assert response.data['source_student']['student_id'] == source_student.student_id
        
        # Check target student info
        assert response.data['target_student']['id'] == target_student.id
        assert response.data['target_student']['first_name'] == target_student.first_name
        assert response.data['target_student']['last_name'] == target_student.last_name
    
    def test_merge_invalid_target_id_type(self, authenticated_client, source_student):
        """Test merge with invalid target_student_id type."""
        url = reverse('attendance:student-merge', kwargs={'pk': source_student.pk})
        data = {'target_student_id': 'invalid'}
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
