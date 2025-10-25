"""
Tests for FaceDetectionService

This module tests the face detection service functionality including:
- Face detection in images
- Coordinate extraction
- Face crop extraction
- Error handling and edge cases
"""

import pytest
import os
import tempfile
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from attendance.services.face_detection import FaceDetectionService, FaceDetection
from attendance.tests.test_helpers import (
    create_test_image,
    create_test_image_with_faces,
    save_test_image,
    create_mock_face_detection,
    create_mock_detections,
    TestImageContext
)


class TestFaceDetection:
    """Tests for the FaceDetection dataclass."""
    
    def test_face_detection_properties(self):
        """Test FaceDetection property accessors."""
        facial_area = {'x': 100, 'y': 150, 'w': 200, 'h': 250}
        detection = FaceDetection(facial_area=facial_area, confidence=0.95)
        
        assert detection.x == 100
        assert detection.y == 150
        assert detection.w == 200
        assert detection.h == 250
        assert detection.confidence == 0.95
    
    def test_coordinates_string(self):
        """Test coordinates_string property."""
        facial_area = {'x': 100, 'y': 150, 'w': 200, 'h': 250}
        detection = FaceDetection(facial_area=facial_area, confidence=0.95)
        
        assert detection.coordinates_string == "100,150,200,250"
    
    def test_bounding_box(self):
        """Test bounding_box property."""
        facial_area = {'x': 100, 'y': 150, 'w': 200, 'h': 250}
        detection = FaceDetection(facial_area=facial_area, confidence=0.95)
        
        bbox = detection.bounding_box
        assert bbox == (100, 150, 200, 250)
        assert isinstance(bbox, tuple)
    
    def test_missing_coordinates(self):
        """Test handling of missing coordinates."""
        facial_area = {}
        detection = FaceDetection(facial_area=facial_area, confidence=0.95)
        
        assert detection.x == 0
        assert detection.y == 0
        assert detection.w == 0
        assert detection.h == 0


class TestFaceDetectionServiceInit:
    """Tests for FaceDetectionService initialization."""
    
    def test_default_initialization(self):
        """Test service initialization with default parameters."""
        service = FaceDetectionService()
        
        assert service.detector_backend == 'retinaface'
        assert service.enforce_detection is False
        assert service.align is True
    
    def test_custom_initialization(self):
        """Test service initialization with custom parameters."""
        service = FaceDetectionService(
            detector_backend='opencv',
            enforce_detection=True,
            align=False
        )
        
        assert service.detector_backend == 'opencv'
        assert service.enforce_detection is True
        assert service.align is False
    
    def test_invalid_backend_raises_error(self):
        """Test that invalid detector backend raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            FaceDetectionService(detector_backend='invalid_backend')
        
        assert 'Unsupported detector backend' in str(exc_info.value)
        assert 'invalid_backend' in str(exc_info.value)
    
    def test_supported_backends(self):
        """Test that all supported backends can be initialized."""
        for backend in FaceDetectionService.SUPPORTED_BACKENDS:
            service = FaceDetectionService(detector_backend=backend)
            assert service.detector_backend == backend


class TestDetectFaces:
    """Tests for face detection functionality."""
    
    def test_detect_faces_file_not_found(self):
        """Test that FileNotFoundError is raised for non-existent files."""
        service = FaceDetectionService()
        
        with pytest.raises(FileNotFoundError) as exc_info:
            service.detect_faces('/path/to/nonexistent/image.jpg')
        
        assert 'Image file not found' in str(exc_info.value)
    
    def test_detect_faces_invalid_path(self):
        """Test that ValueError is raised for directory paths."""
        service = FaceDetectionService()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ValueError) as exc_info:
                service.detect_faces(temp_dir)
            
            assert 'Path is not a file' in str(exc_info.value)
    
    @patch('attendance.services.face_detection.DeepFace')
    def test_detect_faces_success(self, mock_deepface):
        """Test successful face detection."""
        # Mock DeepFace.extract_faces
        mock_deepface.extract_faces.return_value = [
            {
                'facial_area': {'x': 100, 'y': 150, 'w': 200, 'h': 250},
                'confidence': 0.95,
                'face': np.zeros((250, 200, 3))
            },
            {
                'facial_area': {'x': 400, 'y': 100, 'w': 180, 'h': 220},
                'confidence': 0.89,
                'face': np.zeros((220, 180, 3))
            }
        ]
        
        service = FaceDetectionService()
        
        with TestImageContext() as ctx:
            img_path = ctx.create_simple_image()
            detections = service.detect_faces(img_path)
        
        assert len(detections) == 2
        assert all(isinstance(d, FaceDetection) for d in detections)
        
        # Check first detection
        assert detections[0].x == 100
        assert detections[0].y == 150
        assert detections[0].w == 200
        assert detections[0].h == 250
        assert detections[0].confidence == 0.95
        
        # Check second detection
        assert detections[1].x == 400
        assert detections[1].confidence == 0.89
    
    @patch('attendance.services.face_detection.DeepFace')
    def test_detect_faces_with_confidence_filter(self, mock_deepface):
        """Test face detection with confidence filtering."""
        # Mock detections with varying confidence
        mock_deepface.extract_faces.return_value = [
            {
                'facial_area': {'x': 100, 'y': 150, 'w': 200, 'h': 250},
                'confidence': 0.95,
                'face': np.zeros((250, 200, 3))
            },
            {
                'facial_area': {'x': 400, 'y': 100, 'w': 180, 'h': 220},
                'confidence': 0.60,
                'face': np.zeros((220, 180, 3))
            },
            {
                'facial_area': {'x': 300, 'y': 300, 'w': 150, 'h': 180},
                'confidence': 0.45,
                'face': np.zeros((180, 150, 3))
            }
        ]
        
        service = FaceDetectionService()
        
        with TestImageContext() as ctx:
            img_path = ctx.create_simple_image()
            # Filter out detections below 0.7 confidence
            detections = service.detect_faces(img_path, min_confidence=0.7)
        
        # Only the first detection should pass the filter
        assert len(detections) == 1
        assert detections[0].confidence == 0.95
    
    @patch('attendance.services.face_detection.DeepFace')
    def test_detect_faces_no_detections(self, mock_deepface):
        """Test face detection when no faces are found."""
        mock_deepface.extract_faces.return_value = []
        
        service = FaceDetectionService()
        
        with TestImageContext() as ctx:
            img_path = ctx.create_simple_image()
            detections = service.detect_faces(img_path)
        
        assert len(detections) == 0
        assert isinstance(detections, list)
    
    @patch('attendance.services.face_detection.DeepFace')
    def test_detect_faces_deepface_error(self, mock_deepface):
        """Test handling of DeepFace errors."""
        mock_deepface.extract_faces.side_effect = Exception("DeepFace error")
        
        service = FaceDetectionService()
        
        with TestImageContext() as ctx:
            img_path = ctx.create_simple_image()
            
            with pytest.raises(RuntimeError) as exc_info:
                service.detect_faces(img_path)
            
            assert 'Face detection failed' in str(exc_info.value)


class TestExtractFaceCrop:
    """Tests for face crop extraction."""
    
    def test_extract_face_crop_file_not_found(self):
        """Test that extraction fails for non-existent files."""
        service = FaceDetectionService()
        detection = create_mock_face_detection()
        
        with pytest.raises(ValueError) as exc_info:
            service.extract_face_crop('/path/to/nonexistent.jpg', detection)
        
        assert 'Could not read image' in str(exc_info.value)
    
    def test_extract_face_crop_success(self):
        """Test successful face crop extraction."""
        service = FaceDetectionService()
        
        with TestImageContext() as ctx:
            img_path, face_areas = ctx.create_image_with_faces(num_faces=1)
            detection = FaceDetection(facial_area=face_areas[0], confidence=0.95)
            
            crop = service.extract_face_crop(img_path, detection)
            
            assert crop is not None
            assert isinstance(crop, np.ndarray)
            assert crop.shape[0] == face_areas[0]['h']
            assert crop.shape[1] == face_areas[0]['w']
    
    def test_extract_face_crop_with_padding(self):
        """Test face crop extraction with padding."""
        service = FaceDetectionService()
        padding = 10
        
        with TestImageContext() as ctx:
            img_path, face_areas = ctx.create_image_with_faces(num_faces=1)
            detection = FaceDetection(facial_area=face_areas[0], confidence=0.95)
            
            crop = service.extract_face_crop(img_path, detection, padding=padding)
            
            assert crop is not None
            # Crop should be larger due to padding
            assert crop.shape[0] >= face_areas[0]['h']
            assert crop.shape[1] >= face_areas[0]['w']
    
    def test_extract_face_crop_at_boundary(self):
        """Test crop extraction at image boundaries."""
        service = FaceDetectionService()
        
        with TestImageContext() as ctx:
            img_path = ctx.create_simple_image(width=200, height=200)
            # Face at the corner
            detection = FaceDetection(
                facial_area={'x': 0, 'y': 0, 'w': 50, 'h': 50},
                confidence=0.95
            )
            
            crop = service.extract_face_crop(img_path, detection, padding=10)
            
            # Should not crash and return valid crop
            assert crop is not None
            assert crop.size > 0


class TestSaveFaceCrop:
    """Tests for saving face crops."""
    
    def test_save_face_crop_success(self):
        """Test successful face crop saving."""
        service = FaceDetectionService()
        
        # Create a test crop image
        crop_image = create_test_image(100, 100, 3, (200, 150, 150))
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, 'test_crop.jpg')
            
            saved_path = service.save_face_crop(crop_image, output_path)
            
            assert saved_path == output_path
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0
    
    def test_save_face_crop_creates_directory(self):
        """Test that save_face_crop creates the directory if needed."""
        service = FaceDetectionService()
        crop_image = create_test_image(100, 100, 3, (200, 150, 150))
        
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_dir = os.path.join(temp_dir, 'subdir', 'nested')
            output_path = os.path.join(nested_dir, 'test_crop.jpg')
            
            saved_path = service.save_face_crop(crop_image, output_path)
            
            assert os.path.exists(saved_path)
            assert os.path.isdir(nested_dir)


class TestDetectAndExtractCrops:
    """Tests for the combined detect and extract functionality."""
    
    @patch('attendance.services.face_detection.DeepFace')
    def test_detect_and_extract_crops(self, mock_deepface):
        """Test the complete detection and extraction workflow."""
        # Mock DeepFace
        mock_deepface.extract_faces.return_value = [
            {
                'facial_area': {'x': 50, 'y': 50, 'w': 150, 'h': 200},
                'confidence': 0.95,
                'face': np.zeros((200, 150, 3))
            },
            {
                'facial_area': {'x': 400, 'y': 60, 'w': 140, 'h': 190},
                'confidence': 0.89,
                'face': np.zeros((190, 140, 3))
            }
        ]
        
        service = FaceDetectionService()
        
        with TestImageContext() as ctx:
            img_path, _ = ctx.create_image_with_faces(num_faces=2)
            output_dir = ctx.create_temp_dir()
            
            results = service.detect_and_extract_crops(
                image_path=img_path,
                output_dir=output_dir
            )
            
            assert len(results) == 2
            
            # Check that files were created
            for crop_path, detection in results:
                assert os.path.exists(crop_path)
                assert isinstance(detection, FaceDetection)
                assert crop_path.endswith('.jpg')
    
    @patch('attendance.services.face_detection.DeepFace')
    def test_detect_and_extract_no_faces(self, mock_deepface):
        """Test detection and extraction when no faces are found."""
        mock_deepface.extract_faces.return_value = []
        
        service = FaceDetectionService()
        
        with TestImageContext() as ctx:
            img_path = ctx.create_simple_image()
            output_dir = ctx.create_temp_dir()
            
            results = service.detect_and_extract_crops(
                image_path=img_path,
                output_dir=output_dir
            )
            
            assert len(results) == 0
            assert isinstance(results, list)


class TestEdgeCases:
    """Tests for edge cases and error conditions."""
    
    def test_service_import_without_deepface(self):
        """Test that appropriate error is raised when DeepFace is not installed."""
        service = FaceDetectionService()
        
        with TestImageContext() as ctx:
            img_path = ctx.create_simple_image()
            
            # Patch DeepFace to be None to simulate it not being installed
            with patch('attendance.services.face_detection.DeepFace', None):
                with pytest.raises(RuntimeError) as exc_info:
                    service.detect_faces(img_path)
                
                assert 'DeepFace library not installed' in str(exc_info.value)
    
    def test_empty_image_handling(self):
        """Test handling of empty/invalid images."""
        service = FaceDetectionService()
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            temp_path = f.name
            # Write invalid image data
            f.write(b'not an image')
        
        try:
            with pytest.raises(ValueError):
                service.extract_face_crop(temp_path, create_mock_face_detection())
        finally:
            os.unlink(temp_path)
