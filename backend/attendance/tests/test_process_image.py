"""
Integration Tests for Image Processing API

This module contains end-to-end tests for the process_image API endpoint,
testing the complete workflow from image upload to face detection and crop creation.
"""

import pytest
import os
import tempfile
from io import BytesIO
from unittest.mock import patch, Mock
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from PIL import Image as PILImage
from attendance.models import Class, Session, Image, FaceCrop
from attendance.services.face_detection import FaceDetection
from attendance.tests.test_helpers import (
    create_test_image,
    create_test_image_with_faces,
    save_test_image
)


@pytest.fixture
def uploaded_image(db, session1):
    """Fixture to create an Image with actual uploaded file."""
    # Create a simple test image
    img_array = create_test_image(640, 480, 3, (255, 255, 255))
    temp_path = save_test_image(img_array, 'test_upload.jpg')
    
    try:
        # Create an Image instance with the uploaded file
        with open(temp_path, 'rb') as f:
            image_file = SimpleUploadedFile(
                name='test_upload.jpg',
                content=f.read(),
                content_type='image/jpeg'
            )
            
            image_obj = Image.objects.create(
                session=session1,
                original_image_path=image_file
            )
        
        yield image_obj
        
        # Cleanup: delete the uploaded file
        if image_obj.original_image_path:
            image_obj.original_image_path.delete()
        if image_obj.processed_image_path:
            image_obj.processed_image_path.delete()
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@pytest.mark.django_db
class TestProcessImageEndpoint:
    """Tests for the process_image API endpoint."""
    
    def test_process_image_unauthorized(self, api_client, uploaded_image):
        """Test that unauthorized users cannot process images."""
        url = reverse('attendance:image-process-image', kwargs={'pk': uploaded_image.pk})
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_process_image_not_owner(self, another_authenticated_client, uploaded_image):
        """Test that users cannot process images in other users' classes."""
        url = reverse('attendance:image-process-image', kwargs={'pk': uploaded_image.pk})
        response = another_authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_process_image_admin_access(self, admin_authenticated_client, uploaded_image):
        """Test that admins can process any image."""
        url = reverse('attendance:image-process-image', kwargs={'pk': uploaded_image.pk})
        
        with patch('attendance.utils.FaceDetectionService') as mock_service_class:
            # Mock the detection service
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.detect_faces.return_value = []
            
            response = admin_authenticated_client.post(url)
        
        # Admin should have access
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
    
    def test_process_image_already_processed(self, authenticated_client, uploaded_image):
        """Test that already processed images cannot be processed again."""
        # Mark image as processed
        uploaded_image.is_processed = True
        uploaded_image.save()
        
        url = reverse('attendance:image-process-image', kwargs={'pk': uploaded_image.pk})
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'already been processed' in response.data['error']
    
    def test_process_image_invalid_parameters(self, authenticated_client, uploaded_image):
        """Test processing with invalid parameters."""
        url = reverse('attendance:image-process-image', kwargs={'pk': uploaded_image.pk})
        
        # Test with invalid confidence threshold
        response = authenticated_client.post(url, {
            'confidence_threshold': 1.5  # Invalid: should be 0-1
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @patch('attendance.utils.save_processed_image')
    @patch('attendance.utils.FaceDetectionService')
    @patch('attendance.utils.ImageProcessor')
    def test_process_image_no_faces_detected(
        self,
        mock_processor_class,
        mock_service_class,
        mock_save_processed,
        authenticated_client,
        uploaded_image
    ):
        """Test processing an image with no faces detected."""
        # Mock services to return no detections
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.detect_faces.return_value = []
        
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        mock_processor.load_image.return_value = mock_processor
        mock_processor.draw_face_rectangles.return_value = mock_processor
        mock_processor.apply_background_effect.return_value = mock_processor
        mock_processor.save.return_value = None
        
        # Mock save_processed_image to update the image object
        def side_effect_save(img_obj, path):
            img_obj.is_processed = True
            img_obj.processing_date = timezone.now()
            img_obj.processed_image_path = 'processed.jpg'
            img_obj.save()
            img_obj.session.update_processing_status()
            return img_obj
        mock_save_processed.side_effect = side_effect_save
        
        url = reverse('attendance:image-process-image', kwargs={'pk': uploaded_image.pk})
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['faces_detected'] == 0
        assert response.data['crops_created'] == []
        assert response.data['status'] == 'completed'
        
        # Verify image was marked as processed
        uploaded_image.refresh_from_db()
        assert uploaded_image.is_processed is True
    
    @patch('attendance.utils.save_processed_image')
    @patch('attendance.utils.create_face_crop_from_file')
    @patch('attendance.utils.FaceDetectionService')
    @patch('attendance.utils.ImageProcessor')
    def test_process_image_with_faces(
        self,
        mock_processor_class,
        mock_service_class,
        mock_create_crop,
        mock_save_processed,
        authenticated_client,
        uploaded_image
    ):
        """Test processing an image with detected faces."""
        # Create mock detections
        mock_detections = [
            FaceDetection(
                facial_area={'x': 100, 'y': 150, 'w': 200, 'h': 250},
                confidence=0.95
            ),
            FaceDetection(
                facial_area={'x': 400, 'y': 200, 'w': 180, 'h': 220},
                confidence=0.89
            )
        ]
        
        # Mock face detection service
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.detect_faces.return_value = mock_detections
        mock_service.extract_face_crop.return_value = create_test_image(200, 250, 3)
        mock_service.save_face_crop.return_value = None
        
        # Mock image processor
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        mock_processor.load_image.return_value = mock_processor
        mock_processor.draw_face_rectangles.return_value = mock_processor
        mock_processor.apply_background_effect.return_value = mock_processor
        mock_processor.save.return_value = None
        
        # Mock save_processed_image to update the image object
        def side_effect_save(img_obj, path):
            img_obj.is_processed = True
            img_obj.processing_date = timezone.now()
            img_obj.processed_image_path = 'processed.jpg'
            img_obj.save()
            img_obj.session.update_processing_status()
            return img_obj
        mock_save_processed.side_effect = side_effect_save
        
        # Mock create_face_crop_from_file to actually create face crops
        crop_counter = [0]  # Use list to allow mutation in closure
        def side_effect_create_crop(image_obj, crop_file_path, coordinates, confidence_score=None, student=None):
            crop_counter[0] += 1
            crop = FaceCrop.objects.create(
                image=image_obj,
                coordinates=coordinates,
                confidence_score=confidence_score,
                is_identified=False
            )
            return crop
        mock_create_crop.side_effect = side_effect_create_crop
        
        url = reverse('attendance:image-process-image', kwargs={'pk': uploaded_image.pk})
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['faces_detected'] == 2
        assert len(response.data['crops_created']) == 2
        assert response.data['status'] == 'completed'
        
        # Verify image was marked as processed
        uploaded_image.refresh_from_db()
        assert uploaded_image.is_processed is True
        
        # Verify face crops were created
        face_crops = FaceCrop.objects.filter(image=uploaded_image).order_by('id')
        assert face_crops.count() == 2
        
        # Verify crop coordinates (in creation order)
        crop1 = face_crops[0]
        crop2 = face_crops[1]
        assert crop1.coordinates == "100,150,200,250"
        assert crop1.confidence_score == 0.95
        assert crop2.coordinates == "400,200,180,220"
        assert crop2.confidence_score == 0.89
    
    @patch('attendance.utils.FaceDetectionService')
    def test_process_image_detection_error(
        self,
        mock_service_class,
        authenticated_client,
        uploaded_image
    ):
        """Test handling of face detection errors."""
        # Mock service to raise an error
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.detect_faces.side_effect = RuntimeError("Detection failed")
        
        url = reverse('attendance:image-process-image', kwargs={'pk': uploaded_image.pk})
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'Failed to process image' in response.data['error']
        
        # Image should not be marked as processed
        uploaded_image.refresh_from_db()
        assert uploaded_image.is_processed is False
    
    def test_process_image_missing_file(self, authenticated_client, session1):
        """Test processing an image where the file doesn't exist."""
        # Create an Image without an actual file
        image_obj = Image.objects.create(
            session=session1,
            original_image_path='nonexistent.jpg'
        )
        
        url = reverse('attendance:image-process-image', kwargs={'pk': image_obj.pk})
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'not found' in response.data['error']
    
    @patch('attendance.utils.save_processed_image')
    @patch('attendance.utils.FaceDetectionService')
    @patch('attendance.utils.ImageProcessor')
    def test_process_image_custom_parameters(
        self,
        mock_processor_class,
        mock_service_class,
        mock_save_processed,
        authenticated_client,
        uploaded_image
    ):
        """Test processing with custom detection parameters."""
        # Mock services
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.detect_faces.return_value = []
        
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        mock_processor.load_image.return_value = mock_processor
        mock_processor.draw_face_rectangles.return_value = mock_processor
        mock_processor.apply_background_effect.return_value = mock_processor
        mock_processor.save.return_value = None
        
        # Mock save_processed_image to update the image object
        def side_effect_save(img_obj, path):
            img_obj.is_processed = True
            img_obj.processing_date = timezone.now()
            img_obj.processed_image_path = 'processed.jpg'
            img_obj.save()
            img_obj.session.update_processing_status()
            return img_obj
        mock_save_processed.side_effect = side_effect_save
        
        url = reverse('attendance:image-process-image', kwargs={'pk': uploaded_image.pk})
        response = authenticated_client.post(url, {
            'detector_backend': 'opencv',
            'confidence_threshold': 0.8
        })
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify service was called with correct parameters
        mock_service.detect_faces.assert_called_once()
        call_kwargs = mock_service.detect_faces.call_args[1]
        assert call_kwargs['min_confidence'] == 0.8
    
    @patch('attendance.utils.save_processed_image')
    @patch('attendance.utils.FaceDetectionService')
    @patch('attendance.utils.ImageProcessor')
    def test_process_image_updates_session_status(
        self,
        mock_processor_class,
        mock_service_class,
        mock_save_processed,
        authenticated_client,
        uploaded_image
    ):
        """Test that processing an image updates the session status."""
        session = uploaded_image.session
        
        # Create another image in the same session
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            img_array = create_test_image(640, 480, 3)
            PILImage.fromarray(img_array).save(f, 'JPEG')
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as f:
                image_file = SimpleUploadedFile(
                    name='test2.jpg',
                    content=f.read(),
                    content_type='image/jpeg'
                )
                image2 = Image.objects.create(
                    session=session,
                    original_image_path=image_file
                )
            
            # Mock services
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.detect_faces.return_value = []
            mock_service.extract_face_crop.return_value = create_test_image(200, 250, 3)
            mock_service.save_face_crop.return_value = None
            
            mock_processor = Mock()
            mock_processor_class.return_value = mock_processor
            mock_processor.load_image.return_value = mock_processor
            mock_processor.draw_face_rectangles.return_value = mock_processor
            mock_processor.apply_background_effect.return_value = mock_processor
            mock_processor.save.return_value = None
            
            # Mock save_processed_image to actually update the image object
            def side_effect_save(img_obj, path):
                img_obj.is_processed = True
                img_obj.processing_date = timezone.now()
                img_obj.processed_image_path = 'processed.jpg'
                img_obj.save()
                img_obj.session.update_processing_status()
                return img_obj
            mock_save_processed.side_effect = side_effect_save
            
            # Session should not be processed yet
            session.refresh_from_db()
            assert session.is_processed is False
            
            # Process first image
            url1 = reverse('attendance:image-process-image', kwargs={'pk': uploaded_image.pk})
            authenticated_client.post(url1)
            
            session.refresh_from_db()
            assert session.is_processed is False  # Still has unprocessed images
            
            # Process second image
            url2 = reverse('attendance:image-process-image', kwargs={'pk': image2.pk})
            authenticated_client.post(url2)
            
            # Now session should be marked as processed
            session.refresh_from_db()
            assert session.is_processed is True
            
            # Cleanup
            if image2.original_image_path:
                image2.original_image_path.delete()
            if image2.processed_image_path:
                image2.processed_image_path.delete()
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


@pytest.mark.django_db
class TestProcessImageUtils:
    """Tests for the process_image_with_face_detection utility function."""
    
    @patch('attendance.utils.save_processed_image')
    @patch('attendance.utils.create_face_crop_from_file')
    @patch('attendance.utils.FaceDetectionService')
    @patch('attendance.utils.ImageProcessor')
    def test_process_image_utility_success(
        self,
        mock_processor_class,
        mock_service_class,
        mock_create_crop,
        mock_save_processed,
        uploaded_image
    ):
        """Test the utility function directly."""
        from attendance.utils import process_image_with_face_detection
        from attendance.models import FaceCrop
        
        # Create mock detections
        mock_detections = [
            FaceDetection(
                facial_area={'x': 100, 'y': 150, 'w': 200, 'h': 250},
                confidence=0.95
            )
        ]
        
        # Mock services
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.detect_faces.return_value = mock_detections
        mock_service.extract_face_crop.return_value = create_test_image(200, 250, 3)
        mock_service.save_face_crop.return_value = None  # Just needs to not raise
        
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        mock_processor.load_image.return_value = mock_processor
        mock_processor.draw_face_rectangles.return_value = mock_processor
        mock_processor.apply_background_effect.return_value = mock_processor
        mock_processor.save.return_value = None  # Just needs to not raise
        
        # Mock the file-saving utilities
        mock_face_crop = Mock(spec=FaceCrop)
        mock_face_crop.id = 1
        mock_create_crop.return_value = mock_face_crop
        
        # Mock save_processed_image to update the image object
        def side_effect_save(img_obj, path):
            img_obj.is_processed = True
            img_obj.processed_image_path = 'processed.jpg'
            return img_obj
        mock_save_processed.side_effect = side_effect_save
        
        # Call the utility function
        result = process_image_with_face_detection(uploaded_image)
        
        assert result['faces_detected'] == 1
        assert len(result['crops_created']) == 1
        
        # Verify the save functions were called
        mock_save_processed.assert_called_once()
        mock_create_crop.assert_called_once()
    
    def test_process_image_utility_no_file(self, session1):
        """Test utility function with missing image file."""
        from attendance.utils import process_image_with_face_detection
        
        # Create image without file
        image_obj = Image.objects.create(
            session=session1,
            original_image_path='nonexistent.jpg'
        )
        
        with pytest.raises(FileNotFoundError):
            process_image_with_face_detection(image_obj)
    
    def test_process_image_utility_no_path(self, session1):
        """Test utility function with no image path."""
        from attendance.utils import process_image_with_face_detection
        
        # Create image without path
        image_obj = Image.objects.create(session=session1)
        
        with pytest.raises(ValueError):
            process_image_with_face_detection(image_obj)
