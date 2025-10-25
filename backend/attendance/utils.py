"""
Utility functions for handling image processing and file management.

This module provides high-level utilities for:
- Processing images with face detection
- Saving processed images and face crops
- Managing file operations for the attendance system

The module uses the service layer (face_detection and image_processor)
to maintain separation of concerns and enable easier testing.
"""
import os
import tempfile
from typing import Optional, Dict, List
from django.core.files import File
from django.utils import timezone

# Import services at module level for proper mocking in tests
from attendance.services import FaceDetectionService, ImageProcessor


def save_processed_image(image_obj, processed_file_path):
    """
    Save a processed image file to the Image model's processed_image_path field.
    
    Args:
        image_obj: Image model instance
        processed_file_path: Path to the processed image file on disk
    
    Returns:
        The saved Image instance
    
    Raises:
        FileNotFoundError: If processed image file doesn't exist
    """
    if not os.path.exists(processed_file_path):
        raise FileNotFoundError(f"Processed image file not found: {processed_file_path}")
    
    filename = os.path.basename(processed_file_path)
    
    with open(processed_file_path, 'rb') as f:
        image_obj.processed_image_path.save(filename, File(f), save=False)
    
    image_obj.is_processed = True
    image_obj.processing_date = timezone.now()
    image_obj.save()
    
    # Update session processing status
    image_obj.session.update_processing_status()
    
    return image_obj


def save_face_crop(face_crop_obj, crop_file_path):
    """
    Save a face crop image file to the FaceCrop model's crop_image_path field.
    
    Args:
        face_crop_obj: FaceCrop model instance
        crop_file_path: Path to the face crop image file on disk
    
    Returns:
        The saved FaceCrop instance
    
    Raises:
        FileNotFoundError: If face crop file doesn't exist
    """
    if not os.path.exists(crop_file_path):
        raise FileNotFoundError(f"Face crop file not found: {crop_file_path}")
    
    filename = os.path.basename(crop_file_path)
    
    with open(crop_file_path, 'rb') as f:
        face_crop_obj.crop_image_path.save(filename, File(f), save=True)
    
    return face_crop_obj


def create_face_crop_from_file(
    image_obj,
    crop_file_path: str,
    coordinates: str,
    confidence_score: Optional[float] = None,
    student=None
):
    """
    Create a FaceCrop instance from a file on disk.
    
    Args:
        image_obj: Image model instance (parent image)
        crop_file_path: Path to the face crop image file
        coordinates: Coordinate string in format "x,y,width,height"
        confidence_score: Optional confidence score for identification
        student: Optional Student instance if face is identified
    
    Returns:
        Created FaceCrop instance
    """
    from attendance.models import FaceCrop
    
    face_crop = FaceCrop(
        image=image_obj,
        coordinates=coordinates,
        confidence_score=confidence_score,
        student=student,
        is_identified=student is not None
    )
    
    # Save the crop image file
    save_face_crop(face_crop, crop_file_path)
    
    return face_crop


def process_image_with_face_detection(
    image_obj,
    detector_backend: str = 'retinaface',
    min_confidence: float = 0.0,
    apply_background_effect: bool = True,
    rectangle_color: tuple = (0, 255, 0),
    rectangle_thickness: int = 2
) -> Dict[str, any]:
    """
    Process an image using the face detection system and save results.
    
    This function is the main entry point for image processing. It:
    1. Detects faces in the uploaded image
    2. Creates a processed image with rectangles and background effects
    3. Extracts and saves individual face crops
    4. Creates FaceCrop database records
    5. Updates the Image model with processing results
    
    Args:
        image_obj: Image model instance to process
        detector_backend: Backend to use for face detection
            Options: opencv, ssd, dlib, mtcnn, retinaface, mediapipe, yolov8, yunet
        min_confidence: Minimum confidence threshold for face detection (0-1)
        apply_background_effect: Whether to apply grayscale/shadow to background
        rectangle_color: BGR color tuple for face rectangles
        rectangle_thickness: Thickness of rectangle borders in pixels
    
    Returns:
        dict with processing results:
        {
            'faces_detected': int - Number of faces found,
            'crops_created': list - List of FaceCrop IDs,
            'processed_image_url': str - URL to processed image
        }
    
    Raises:
        FileNotFoundError: If original image file doesn't exist
        ValueError: If image processing fails
        RuntimeError: If face detection library is not available
    
    Example:
        >>> result = process_image_with_face_detection(
        ...     image_obj=my_image,
        ...     detector_backend='retinaface',
        ...     min_confidence=0.7
        ... )
        >>> print(f"Found {result['faces_detected']} faces")
    """
    # Validate that the image file exists
    if not image_obj.original_image_path:
        raise ValueError("Image object has no original_image_path")
    
    original_path = image_obj.original_image_path.path
    
    if not os.path.exists(original_path):
        raise FileNotFoundError(f"Original image file not found: {original_path}")
    
    # Initialize services
    face_detector = FaceDetectionService(
        detector_backend=detector_backend,
        enforce_detection=False
    )
    
    # Create temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Step 1: Detect faces
        detections = face_detector.detect_faces(
            image_path=original_path,
            min_confidence=min_confidence
        )
        
        # Step 2: Create processed image with rectangles and effects
        processed_image_path = os.path.join(
            temp_dir,
            f"processed_{os.path.basename(original_path)}"
        )
        
        image_processor = ImageProcessor(
            rectangle_color=rectangle_color,
            rectangle_thickness=rectangle_thickness
        )
        
        image_processor.load_image(original_path)
        image_processor.draw_face_rectangles(detections)
        
        if apply_background_effect:
            image_processor.apply_background_effect()
        
        image_processor.save(processed_image_path)
        
        # Step 3: Save the processed image to the model
        save_processed_image(image_obj, processed_image_path)
        
        # Step 4: Extract and save face crops
        crops_dir = os.path.join(temp_dir, "crops")
        os.makedirs(crops_dir, exist_ok=True)
        
        crop_ids = []
        for idx, detection in enumerate(detections, start=1):
            # Extract the crop using the detection service
            crop_image = face_detector.extract_face_crop(
                image_path=original_path,
                detection=detection,
                padding=0
            )
            
            # Save crop to temporary file
            crop_filename = f"{os.path.splitext(os.path.basename(original_path))[0]}_face{idx}.jpg"
            crop_path = os.path.join(crops_dir, crop_filename)
            face_detector.save_face_crop(crop_image, crop_path)
            
            # Create FaceCrop database record
            face_crop = create_face_crop_from_file(
                image_obj=image_obj,
                crop_file_path=crop_path,
                coordinates=detection.coordinates_string,
                confidence_score=detection.confidence
            )
            crop_ids.append(face_crop.id)
    
    return {
        'faces_detected': len(detections),
        'crops_created': crop_ids,
        'processed_image_url': image_obj.processed_image_path.url if image_obj.processed_image_path else None
    }


# Legacy compatibility function - deprecated
def process_image_with_face_detection_legacy(image_obj, extractor=None, min_face_size=20, confidence_threshold=0.5):
    """
    DEPRECATED: Legacy function for backward compatibility with core.face.extractor.
    
    This function is maintained for backward compatibility but will be removed
    in a future version. Use process_image_with_face_detection() instead.
    
    Args:
        image_obj: Image model instance to process
        extractor: FaceExtractor instance (optional, will create if not provided)
        min_face_size: Minimum face size for detection (not used)
        confidence_threshold: Confidence threshold for face detection
    
    Returns:
        dict with processing results
    """
    import warnings
    warnings.warn(
        "process_image_with_face_detection_legacy is deprecated. "
        "Use process_image_with_face_detection instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Call the new implementation
    return process_image_with_face_detection(
        image_obj=image_obj,
        min_confidence=confidence_threshold
    )
