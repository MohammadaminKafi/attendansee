"""
Face Detection Service

This module provides face detection functionality using DeepFace library.
It's designed to be independent of the core module and follows SOLID principles.

Design Patterns:
- Strategy Pattern: Different detector backends can be easily swapped
- Dependency Injection: Dependencies are passed in, not hard-coded
- Single Responsibility: Only handles face detection logic
"""

from typing import List, Dict, Optional, Tuple
import os
from dataclasses import dataclass

# Optional dependency - imported at module level for testability
try:
    from deepface import DeepFace
except ImportError:
    DeepFace = None


@dataclass
class FaceDetection:
    """
    Data class representing a detected face.
    
    Attributes:
        facial_area: Dictionary with x, y, w, h coordinates
        confidence: Detection confidence score (0-1)
        face_image: Optional numpy array of the cropped face
    """
    facial_area: Dict[str, int]
    confidence: float
    face_image: Optional[object] = None  # numpy array
    
    @property
    def x(self) -> int:
        """Get x coordinate of face bounding box."""
        return self.facial_area.get('x', 0)
    
    @property
    def y(self) -> int:
        """Get y coordinate of face bounding box."""
        return self.facial_area.get('y', 0)
    
    @property
    def w(self) -> int:
        """Get width of face bounding box."""
        return self.facial_area.get('w', 0)
    
    @property
    def h(self) -> int:
        """Get height of face bounding box."""
        return self.facial_area.get('h', 0)
    
    @property
    def coordinates_string(self) -> str:
        """Get coordinates as comma-separated string: 'x,y,w,h'."""
        return f"{self.x},{self.y},{self.w},{self.h}"
    
    @property
    def bounding_box(self) -> Tuple[int, int, int, int]:
        """Get bounding box as tuple (x, y, w, h)."""
        return (self.x, self.y, self.w, self.h)


class FaceDetectionService:
    """
    Service for detecting faces in images using DeepFace.
    
    This service provides a clean abstraction over the DeepFace library,
    making it easy to:
    - Detect faces in images
    - Extract face regions
    - Handle detection errors gracefully
    - Swap detection backends
    
    Example:
        >>> service = FaceDetectionService(detector_backend='retinaface')
        >>> detections = service.detect_faces('/path/to/image.jpg')
        >>> print(f"Found {len(detections)} faces")
    """
    
    # Supported detector backends
    SUPPORTED_BACKENDS = [
        'opencv',
        'ssd',
        'dlib',
        'mtcnn',
        'retinaface',
        'mediapipe',
        'yolov8',
        'yunet',
        'fastmtcnn'
    ]
    
    def __init__(
        self,
        detector_backend: str = 'retinaface',
        enforce_detection: bool = False,
        align: bool = True
    ):
        """
        Initialize the face detection service.
        
        Args:
            detector_backend: Backend to use for detection
                Options: opencv, ssd, dlib, mtcnn, retinaface, mediapipe, yolov8, yunet, fastmtcnn
            enforce_detection: If True, raise error when no face is detected
            align: If True, align detected faces
        
        Raises:
            ValueError: If an unsupported detector backend is specified
        """
        if detector_backend not in self.SUPPORTED_BACKENDS:
            raise ValueError(
                f"Unsupported detector backend: {detector_backend}. "
                f"Supported backends: {', '.join(self.SUPPORTED_BACKENDS)}"
            )
        
        self.detector_backend = detector_backend
        self.enforce_detection = enforce_detection
        self.align = align
    
    def detect_faces(
        self,
        image_path: str,
        min_confidence: float = 0.0
    ) -> List[FaceDetection]:
        """
        Detect faces in an image.
        
        Args:
            image_path: Path to the image file
            min_confidence: Minimum confidence threshold for detections (0-1)
        
        Returns:
            List of FaceDetection objects
        
        Raises:
            FileNotFoundError: If the image file doesn't exist
            ValueError: If image cannot be loaded or processed
            RuntimeError: If detection fails
        """
        # Validate image path
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        if not os.path.isfile(image_path):
            raise ValueError(f"Path is not a file: {image_path}")
        
        try:
            # Check if DeepFace is available
            if DeepFace is None:
                raise RuntimeError("DeepFace library not installed. Install it with: pip install deepface")
            
            # Perform face detection
            raw_detections = DeepFace.extract_faces(
                img_path=image_path,
                detector_backend=self.detector_backend,
                enforce_detection=self.enforce_detection,
                align=self.align
            )
            
            # Convert to our FaceDetection objects
            detections = []
            for det in raw_detections:
                facial_area = det.get('facial_area', {})
                confidence = det.get('confidence', 1.0)
                
                # Filter by confidence threshold
                if confidence >= min_confidence:
                    face_detection = FaceDetection(
                        facial_area=facial_area,
                        confidence=confidence,
                        face_image=det.get('face')
                    )
                    detections.append(face_detection)
            
            return detections
        
        except ImportError as e:
            raise RuntimeError(
                "DeepFace library not installed. "
                "Please install it with: pip install deepface"
            ) from e
        
        except Exception as e:
            raise RuntimeError(
                f"Face detection failed for image {image_path}: {str(e)}"
            ) from e
    
    def extract_face_crop(
        self,
        image_path: str,
        detection: FaceDetection,
        padding: int = 0
    ) -> object:
        """
        Extract a face crop from an image based on detection coordinates.
        
        Args:
            image_path: Path to the source image
            detection: FaceDetection object with coordinates
            padding: Additional padding around the face (in pixels)
        
        Returns:
            numpy array of the cropped face image
        
        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If crop extraction fails
        """
        try:
            import cv2
            import numpy as np
            
            # Read the image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not read image: {image_path}")
            
            height, width = img.shape[:2]
            
            # Get coordinates with padding
            x = max(0, detection.x - padding)
            y = max(0, detection.y - padding)
            w = min(width - x, detection.w + 2 * padding)
            h = min(height - y, detection.h + 2 * padding)
            
            # Extract the crop
            crop = img[y:y+h, x:x+w]
            
            if crop.size == 0:
                raise ValueError("Extracted crop is empty")
            
            return crop
        
        except ImportError as e:
            raise RuntimeError(
                "OpenCV not installed. Please install it with: pip install opencv-python"
            ) from e
        except Exception as e:
            raise ValueError(f"Failed to extract face crop: {str(e)}") from e
    
    def save_face_crop(
        self,
        crop_image: object,
        output_path: str
    ) -> str:
        """
        Save a face crop to disk.
        
        Args:
            crop_image: numpy array of the face image
            output_path: Path where to save the crop
        
        Returns:
            Path to the saved image
        
        Raises:
            ValueError: If saving fails
        """
        try:
            import cv2
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save the image
            success = cv2.imwrite(output_path, crop_image)
            
            if not success:
                raise ValueError(f"Failed to save image to {output_path}")
            
            return output_path
        
        except ImportError as e:
            raise RuntimeError(
                "OpenCV not installed. Please install it with: pip install opencv-python"
            ) from e
        except Exception as e:
            raise ValueError(f"Failed to save face crop: {str(e)}") from e
    
    def detect_and_extract_crops(
        self,
        image_path: str,
        output_dir: str,
        min_confidence: float = 0.0,
        padding: int = 0
    ) -> List[Tuple[str, FaceDetection]]:
        """
        Detect faces and save individual crops to disk.
        
        This is a convenience method that combines detection and extraction.
        
        Args:
            image_path: Path to the source image
            output_dir: Directory where to save face crops
            min_confidence: Minimum confidence threshold
            padding: Additional padding around faces
        
        Returns:
            List of tuples (crop_path, FaceDetection)
        
        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If processing fails
        """
        # Detect faces
        detections = self.detect_faces(image_path, min_confidence)
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract and save each crop
        saved_crops = []
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        
        for idx, detection in enumerate(detections, start=1):
            # Extract the crop
            crop_image = self.extract_face_crop(image_path, detection, padding)
            
            # Generate output filename
            crop_filename = f"{base_name}_face{idx}.jpg"
            crop_path = os.path.join(output_dir, crop_filename)
            
            # Save the crop
            self.save_face_crop(crop_image, crop_path)
            
            saved_crops.append((crop_path, detection))
        
        return saved_crops
