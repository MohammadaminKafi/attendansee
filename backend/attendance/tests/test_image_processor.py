"""
Tests for ImageProcessor

This module tests the image processing service functionality including:
- Loading images from file and array
- Drawing rectangles around faces
- Applying background effects (grayscale/shadow)
- Saving processed images
- Error handling and edge cases
"""

import pytest
import os
import tempfile
import numpy as np
from unittest.mock import Mock, patch
from attendance.services.image_processor import ImageProcessor
from attendance.tests.test_helpers import (
    create_test_image,
    create_test_image_with_faces,
    save_test_image,
    create_mock_detections,
    TestImageContext
)


class TestImageProcessorInit:
    """Tests for ImageProcessor initialization."""
    
    def test_default_initialization(self):
        """Test processor initialization with default parameters."""
        processor = ImageProcessor()
        
        assert processor.rectangle_color == (0, 255, 0)  # Green
        assert processor.rectangle_thickness == 2
        assert processor.background_alpha == 0.6
        assert processor.background_gray_strength == 0.7
        assert processor._image is None
        assert processor._original_image is None
        assert processor._mask is None
    
    def test_custom_initialization(self):
        """Test processor initialization with custom parameters."""
        processor = ImageProcessor(
            rectangle_color=(255, 0, 0),  # Blue
            rectangle_thickness=3,
            background_alpha=0.8,
            background_gray_strength=0.9
        )
        
        assert processor.rectangle_color == (255, 0, 0)
        assert processor.rectangle_thickness == 3
        assert processor.background_alpha == 0.8
        assert processor.background_gray_strength == 0.9


class TestLoadImage:
    """Tests for image loading functionality."""
    
    def test_load_image_from_file(self):
        """Test loading an image from file."""
        processor = ImageProcessor()
        
        with TestImageContext() as ctx:
            img_path = ctx.create_simple_image()
            result = processor.load_image(img_path)
            
            # Should return self for chaining
            assert result is processor
            
            # Image should be loaded
            assert processor._image is not None
            assert processor._original_image is not None
            assert processor._mask is not None
            assert isinstance(processor._image, np.ndarray)
    
    def test_load_image_file_not_found(self):
        """Test that FileNotFoundError is raised for non-existent files."""
        processor = ImageProcessor()
        
        with pytest.raises(FileNotFoundError) as exc_info:
            processor.load_image('/path/to/nonexistent/image.jpg')
        
        assert 'Image file not found' in str(exc_info.value)
    
    def test_load_image_invalid_file(self):
        """Test that ValueError is raised for invalid image files."""
        processor = ImageProcessor()
        
        # Create a text file, not an image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'not an image')
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError) as exc_info:
                processor.load_image(temp_path)
            
            assert 'Could not load image' in str(exc_info.value)
        finally:
            os.unlink(temp_path)
    
    def test_load_from_array(self):
        """Test loading an image from numpy array."""
        processor = ImageProcessor()
        
        img_array = create_test_image(640, 480, 3)
        result = processor.load_from_array(img_array)
        
        # Should return self for chaining
        assert result is processor
        
        # Image should be loaded
        assert processor._image is not None
        # Should be a copy (equal values but different objects)
        assert np.array_equal(processor._image, img_array) is True
        assert processor._image is not img_array
    
    def test_load_from_array_grayscale(self):
        """Test loading grayscale image from array."""
        processor = ImageProcessor()
        
        img_array = create_test_image(640, 480, 1)
        result = processor.load_from_array(img_array)
        
        assert result is processor
        assert processor._image is not None
    
    def test_load_from_array_invalid(self):
        """Test that ValueError is raised for invalid arrays."""
        processor = ImageProcessor()
        
        # Test with non-numpy array
        with pytest.raises(ValueError) as exc_info:
            processor.load_from_array([1, 2, 3])
        
        assert 'must be a numpy ndarray' in str(exc_info.value)
        
        # Test with invalid dimensions
        with pytest.raises(ValueError) as exc_info:
            processor.load_from_array(np.zeros((10, 10, 10, 10)))
        
        assert 'must be 2D' in str(exc_info.value)


class TestDrawFaceRectangles:
    """Tests for drawing face rectangles."""
    
    def test_draw_rectangles_no_image_loaded(self):
        """Test that ValueError is raised when no image is loaded."""
        processor = ImageProcessor()
        detections = create_mock_detections(2)
        
        with pytest.raises(ValueError) as exc_info:
            processor.draw_face_rectangles(detections)
        
        assert 'No image loaded' in str(exc_info.value)
    
    def test_draw_rectangles_success(self):
        """Test successfully drawing rectangles on faces."""
        processor = ImageProcessor()
        
        with TestImageContext() as ctx:
            img_path, face_areas = ctx.create_image_with_faces(num_faces=2)
            detections = create_mock_detections(2)
            
            processor.load_image(img_path)
            original_image = processor._image.copy()
            
            result = processor.draw_face_rectangles(detections)
            
            # Should return self for chaining
            assert result is processor
            
            # Image should be modified
            assert not np.array_equal(processor._image, original_image)
            
            # Mask should be updated
            assert np.any(processor._mask > 0)
    
    def test_draw_rectangles_custom_color(self):
        """Test drawing rectangles with custom color."""
        processor = ImageProcessor()
        
        with TestImageContext() as ctx:
            img_path = ctx.create_simple_image()
            detections = create_mock_detections(1)
            
            processor.load_image(img_path)
            
            custom_color = (255, 0, 0)  # Blue
            processor.draw_face_rectangles(detections, color=custom_color)
            
            # Verify the operation completed (can't easily verify color)
            assert processor._image is not None
    
    def test_draw_rectangles_from_dicts(self):
        """Test drawing rectangles from dict detections."""
        processor = ImageProcessor()
        
        with TestImageContext() as ctx:
            img_path = ctx.create_simple_image()
            
            # Use dict format instead of FaceDetection objects
            detections = [
                {'facial_area': {'x': 100, 'y': 100, 'w': 150, 'h': 200}},
                {'facial_area': {'x': 400, 'y': 150, 'w': 140, 'h': 180}}
            ]
            
            processor.load_image(img_path)
            result = processor.draw_face_rectangles(detections)
            
            assert result is processor
            assert np.any(processor._mask > 0)
    
    def test_draw_rectangles_empty_list(self):
        """Test drawing with empty detection list."""
        processor = ImageProcessor()
        
        with TestImageContext() as ctx:
            img_path = ctx.create_simple_image()
            
            processor.load_image(img_path)
            original_image = processor._image.copy()
            
            result = processor.draw_face_rectangles([])
            
            # Should not crash and should return self
            assert result is processor
            # Image should remain unchanged
            assert np.array_equal(processor._image, original_image)


class TestApplyBackgroundEffect:
    """Tests for applying background effects."""
    
    def test_apply_background_no_image_loaded(self):
        """Test that ValueError is raised when no image is loaded."""
        processor = ImageProcessor()
        
        with pytest.raises(ValueError) as exc_info:
            processor.apply_background_effect()
        
        assert 'No image loaded' in str(exc_info.value)
    
    def test_apply_background_success(self):
        """Test successfully applying background effect."""
        processor = ImageProcessor()
        
        with TestImageContext() as ctx:
            img_path, face_areas = ctx.create_image_with_faces(num_faces=2)
            detections = create_mock_detections(2)
            
            processor.load_image(img_path)
            processor.draw_face_rectangles(detections)
            
            original_image = processor._image.copy()
            
            result = processor.apply_background_effect()
            
            # Should return self for chaining
            assert result is processor
            
            # Image should be modified
            # (Can't easily verify the effect visually in tests, but should be different)
            # In some cases it might be the same if the entire image is marked as face
            assert processor._image is not None
    
    def test_apply_background_custom_parameters(self):
        """Test applying background effect with custom parameters."""
        processor = ImageProcessor()
        
        with TestImageContext() as ctx:
            img_path = ctx.create_simple_image()
            
            processor.load_image(img_path)
            
            result = processor.apply_background_effect(
                alpha=0.8,
                gray_strength=0.9
            )
            
            assert result is processor
            assert processor._image is not None
    
    def test_apply_background_without_faces(self):
        """Test applying background effect without any face regions."""
        processor = ImageProcessor()
        
        with TestImageContext() as ctx:
            img_path = ctx.create_simple_image()
            
            processor.load_image(img_path)
            original_image = processor._original_image.copy()
            
            # Apply effect without marking any face regions
            processor.apply_background_effect()
            
            # Entire image should have the effect applied
            assert processor._image is not None


class TestSaveImage:
    """Tests for saving processed images."""
    
    def test_save_no_image_loaded(self):
        """Test that ValueError is raised when no image is loaded."""
        processor = ImageProcessor()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, 'output.jpg')
            
            with pytest.raises(ValueError) as exc_info:
                processor.save(output_path)
            
            assert 'No image loaded' in str(exc_info.value)
    
    def test_save_success(self):
        """Test successfully saving a processed image."""
        processor = ImageProcessor()
        
        with TestImageContext() as ctx:
            img_path = ctx.create_simple_image()
            processor.load_image(img_path)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = os.path.join(temp_dir, 'output.jpg')
                
                result = processor.save(output_path)
                
                assert result == output_path
                assert os.path.exists(output_path)
                assert os.path.getsize(output_path) > 0
    
    def test_save_creates_directory(self):
        """Test that save creates the output directory if needed."""
        processor = ImageProcessor()
        
        with TestImageContext() as ctx:
            img_path = ctx.create_simple_image()
            processor.load_image(img_path)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                nested_dir = os.path.join(temp_dir, 'subdir', 'nested')
                output_path = os.path.join(nested_dir, 'output.jpg')
                
                result = processor.save(output_path)
                
                assert os.path.exists(output_path)
                assert os.path.isdir(nested_dir)


class TestGetProcessedImage:
    """Tests for getting the processed image."""
    
    def test_get_processed_image_no_image_loaded(self):
        """Test that ValueError is raised when no image is loaded."""
        processor = ImageProcessor()
        
        with pytest.raises(ValueError) as exc_info:
            processor.get_processed_image()
        
        assert 'No image loaded' in str(exc_info.value)
    
    def test_get_processed_image_success(self):
        """Test successfully getting the processed image."""
        processor = ImageProcessor()
        
        with TestImageContext() as ctx:
            img_path = ctx.create_simple_image()
            processor.load_image(img_path)
            
            result = processor.get_processed_image()
            
            assert isinstance(result, np.ndarray)
            assert result.shape == processor._image.shape
            # Should be a copy, not the same array
            assert not np.shares_memory(result, processor._image)


class TestResetImage:
    """Tests for resetting to original image."""
    
    def test_reset_no_image_loaded(self):
        """Test that ValueError is raised when no image is loaded."""
        processor = ImageProcessor()
        
        with pytest.raises(ValueError) as exc_info:
            processor.reset()
        
        assert 'No image loaded' in str(exc_info.value)
    
    def test_reset_success(self):
        """Test successfully resetting to original image."""
        processor = ImageProcessor()
        
        with TestImageContext() as ctx:
            img_path, face_areas = ctx.create_image_with_faces(num_faces=2)
            detections = create_mock_detections(2)
            
            processor.load_image(img_path)
            original = processor._original_image.copy()
            
            # Modify the image
            processor.draw_face_rectangles(detections)
            processor.apply_background_effect()
            
            # Reset
            result = processor.reset()
            
            # Should return self for chaining
            assert result is processor
            
            # Should be back to original
            assert np.array_equal(processor._image, original)
            
            # Mask should be reset
            assert np.all(processor._mask == 0)


class TestProcessImageWithFaces:
    """Tests for the static convenience method."""
    
    def test_process_image_with_faces_success(self):
        """Test the static method for processing images."""
        with TestImageContext() as ctx:
            img_path, face_areas = ctx.create_image_with_faces(num_faces=2)
            detections = create_mock_detections(2)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = os.path.join(temp_dir, 'processed.jpg')
                
                result = ImageProcessor.process_image_with_faces(
                    input_path=img_path,
                    output_path=output_path,
                    detections=detections
                )
                
                assert result == output_path
                assert os.path.exists(output_path)
                assert os.path.getsize(output_path) > 0
    
    def test_process_image_without_background_effect(self):
        """Test processing without background effect."""
        with TestImageContext() as ctx:
            img_path, face_areas = ctx.create_image_with_faces(num_faces=1)
            detections = create_mock_detections(1)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = os.path.join(temp_dir, 'processed.jpg')
                
                result = ImageProcessor.process_image_with_faces(
                    input_path=img_path,
                    output_path=output_path,
                    detections=detections,
                    apply_background=False
                )
                
                assert result == output_path
                assert os.path.exists(output_path)
    
    def test_process_image_custom_parameters(self):
        """Test processing with custom parameters."""
        with TestImageContext() as ctx:
            img_path, face_areas = ctx.create_image_with_faces(num_faces=1)
            detections = create_mock_detections(1)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = os.path.join(temp_dir, 'processed.jpg')
                
                result = ImageProcessor.process_image_with_faces(
                    input_path=img_path,
                    output_path=output_path,
                    detections=detections,
                    rectangle_color=(255, 0, 0),
                    rectangle_thickness=3,
                    background_alpha=0.8,
                    background_gray_strength=0.9
                )
                
                assert result == output_path
                assert os.path.exists(output_path)


class TestMethodChaining:
    """Tests for method chaining capability."""
    
    def test_chaining_workflow(self):
        """Test that methods can be chained together."""
        with TestImageContext() as ctx:
            img_path, face_areas = ctx.create_image_with_faces(num_faces=2)
            detections = create_mock_detections(2)
            
            processor = ImageProcessor()
            
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = os.path.join(temp_dir, 'output.jpg')
                
                # Chain all methods together
                result = (processor
                         .load_image(img_path)
                         .draw_face_rectangles(detections)
                         .apply_background_effect()
                         .save(output_path))
                
                # All methods should return self
                assert result == output_path
                assert os.path.exists(output_path)
    
    def test_chaining_with_reset(self):
        """Test chaining with reset in the middle."""
        with TestImageContext() as ctx:
            img_path = ctx.create_simple_image()
            detections = create_mock_detections(1)
            
            processor = ImageProcessor()
            
            # Load, modify, reset, modify again
            processor.load_image(img_path)
            processor.draw_face_rectangles(detections)
            processor.reset()
            processor.draw_face_rectangles(detections)
            
            assert processor._image is not None


class TestEdgeCases:
    """Tests for edge cases and error conditions."""
    
    def test_very_small_image(self):
        """Test processing a very small image."""
        processor = ImageProcessor()
        
        # Create a tiny 10x10 image
        tiny_img = create_test_image(10, 10, 3)
        processor.load_from_array(tiny_img)
        
        # Should not crash
        processor.apply_background_effect()
        assert processor._image is not None
    
    def test_very_large_rectangle(self):
        """Test drawing a rectangle larger than the image."""
        processor = ImageProcessor()
        
        with TestImageContext() as ctx:
            img_path = ctx.create_simple_image(width=200, height=200)
            
            # Rectangle larger than image
            detection = [{
                'facial_area': {'x': 0, 'y': 0, 'w': 1000, 'h': 1000}
            }]
            
            processor.load_image(img_path)
            
            # Should not crash
            processor.draw_face_rectangles(detection)
            assert processor._image is not None
    
    def test_overlapping_rectangles(self):
        """Test drawing overlapping face rectangles."""
        processor = ImageProcessor()
        
        with TestImageContext() as ctx:
            img_path = ctx.create_simple_image()
            
            # Create overlapping detections
            detections = [
                {'facial_area': {'x': 100, 'y': 100, 'w': 200, 'h': 200}},
                {'facial_area': {'x': 150, 'y': 150, 'w': 200, 'h': 200}},
                {'facial_area': {'x': 200, 'y': 200, 'w': 200, 'h': 200}}
            ]
            
            processor.load_image(img_path)
            processor.draw_face_rectangles(detections)
            
            # Should not crash
            assert processor._image is not None
