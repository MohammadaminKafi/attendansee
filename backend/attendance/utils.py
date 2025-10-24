"""
Utility functions for handling image processing and file management.
"""
import os
from django.core.files import File
from django.core.files.base import ContentFile
from pathlib import Path


def save_processed_image(image_obj, processed_file_path):
    """
    Save a processed image file to the Image model's processed_image_path field.
    
    Args:
        image_obj: Image model instance
        processed_file_path: Path to the processed image file on disk
    
    Returns:
        The saved Image instance
    """
    if not os.path.exists(processed_file_path):
        raise FileNotFoundError(f"Processed image file not found: {processed_file_path}")
    
    filename = os.path.basename(processed_file_path)
    
    with open(processed_file_path, 'rb') as f:
        image_obj.processed_image_path.save(filename, File(f), save=False)
    
    image_obj.is_processed = True
    image_obj.save()
    
    return image_obj


def save_face_crop(face_crop_obj, crop_file_path):
    """
    Save a face crop image file to the FaceCrop model's crop_image_path field.
    
    Args:
        face_crop_obj: FaceCrop model instance
        crop_file_path: Path to the face crop image file on disk
    
    Returns:
        The saved FaceCrop instance
    """
    if not os.path.exists(crop_file_path):
        raise FileNotFoundError(f"Face crop file not found: {crop_file_path}")
    
    filename = os.path.basename(crop_file_path)
    
    with open(crop_file_path, 'rb') as f:
        face_crop_obj.crop_image_path.save(filename, File(f), save=True)
    
    return face_crop_obj


def create_face_crop_from_file(image_obj, crop_file_path, coordinates, confidence_score=None, student=None):
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


def process_image_with_face_detection(image_obj, extractor=None, min_face_size=20, confidence_threshold=0.5):
    """
    Process an image using the face detection system and save results.
    
    This function integrates with the core face recognition module to:
    1. Detect faces in the uploaded image
    2. Draw rectangles on the processed image
    3. Extract and save face crops
    4. Create FaceCrop database records
    
    Args:
        image_obj: Image model instance to process
        extractor: FaceExtractor instance (optional, will create if not provided)
        min_face_size: Minimum face size for detection
        confidence_threshold: Confidence threshold for face detection
    
    Returns:
        dict with processing results:
        {
            'faces_detected': int,
            'crops_created': list of FaceCrop ids,
            'processed_image_url': str
        }
    """
    from core.face.extractor import FaceExtractor
    import tempfile
    
    if extractor is None:
        extractor = FaceExtractor()
    
    # Get the path to the original uploaded image
    original_path = image_obj.original_image_path.path
    
    # Create temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Define output paths
        processed_image_path = os.path.join(temp_dir, f"processed_{os.path.basename(original_path)}")
        crops_dir = os.path.join(temp_dir, "crops")
        
        # Extract faces and save crops
        saved_crops = extractor.extract_and_save(
            img_path=original_path,
            output_image_path=processed_image_path,
            crops_dir=crops_dir
        )
        
        # Save the processed image (with rectangles) to the model
        save_processed_image(image_obj, processed_image_path)
        
        # Create FaceCrop objects for each detected face
        crop_ids = []
        for crop_path, metadata in saved_crops:
            # Extract coordinates from metadata
            facial_area = metadata.get('facial_area', {})
            x = facial_area.get('x', 0)
            y = facial_area.get('y', 0)
            w = facial_area.get('w', 0)
            h = facial_area.get('h', 0)
            coordinates = f"{x},{y},{w},{h}"
            
            # Create FaceCrop instance
            face_crop = create_face_crop_from_file(
                image_obj=image_obj,
                crop_file_path=crop_path,
                coordinates=coordinates
            )
            crop_ids.append(face_crop.id)
    
    return {
        'faces_detected': len(saved_crops),
        'crops_created': crop_ids,
        'processed_image_url': image_obj.processed_image_path.url if image_obj.processed_image_path else None
    }
