"""
Test utilities for creating mock images and face detections.

This module provides helper functions to create test images and mock data
for testing face detection and image processing functionality.
"""

import os
import tempfile
import numpy as np
from typing import Tuple, List
from attendance.services.face_detection import FaceDetection


def create_test_image(
    width: int = 640,
    height: int = 480,
    channels: int = 3,
    color: Tuple[int, int, int] = (255, 255, 255)
) -> np.ndarray:
    """
    Create a test image as a numpy array.
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        channels: Number of color channels (3 for BGR, 1 for grayscale)
        color: BGR color tuple for the image
    
    Returns:
        Numpy array representing the image
    """
    if channels == 1:
        return np.full((height, width), color[0], dtype=np.uint8)
    else:
        img = np.zeros((height, width, channels), dtype=np.uint8)
        img[:] = color
        return img


def create_test_image_with_faces(
    width: int = 640,
    height: int = 480,
    num_faces: int = 2
) -> Tuple[np.ndarray, List[dict]]:
    """
    Create a test image with mock face regions.
    
    This creates a white image with colored rectangles representing faces.
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        num_faces: Number of face regions to create
    
    Returns:
        Tuple of (image array, list of facial_area dicts)
    """
    import cv2
    
    # Create white background
    img = create_test_image(width, height, 3, (255, 255, 255))
    
    face_areas = []
    
    # Create face regions
    if num_faces >= 1:
        # First face: top-left
        x1, y1, w1, h1 = 50, 50, 150, 200
        cv2.rectangle(img, (x1, y1), (x1+w1, y1+h1), (200, 150, 150), -1)
        face_areas.append({'x': x1, 'y': y1, 'w': w1, 'h': h1})
    
    if num_faces >= 2:
        # Second face: top-right
        x2, y2, w2, h2 = 400, 60, 140, 190
        cv2.rectangle(img, (x2, y2), (x2+w2, y2+h2), (150, 200, 150), -1)
        face_areas.append({'x': x2, 'y': y2, 'w': w2, 'h': h2})
    
    if num_faces >= 3:
        # Third face: bottom-center
        x3, y3, w3, h3 = 250, 280, 160, 180
        cv2.rectangle(img, (x3, y3), (x3+w3, y3+h3), (150, 150, 200), -1)
        face_areas.append({'x': x3, 'y': y3, 'w': w3, 'h': h3})
    
    return img, face_areas


def save_test_image(image: np.ndarray, filename: str = None) -> str:
    """
    Save a test image to a temporary file.
    
    Args:
        image: Numpy array representing the image
        filename: Optional filename (will use temp name if not provided)
    
    Returns:
        Path to the saved image file
    """
    import cv2
    
    if filename is None:
        fd, temp_path = tempfile.mkstemp(suffix='.jpg')
        os.close(fd)
    else:
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, filename)
    
    cv2.imwrite(temp_path, image)
    return temp_path


def create_mock_face_detection(
    x: int = 100,
    y: int = 100,
    w: int = 150,
    h: int = 200,
    confidence: float = 0.95
) -> FaceDetection:
    """
    Create a mock FaceDetection object.
    
    Args:
        x: X coordinate of face bounding box
        y: Y coordinate of face bounding box
        w: Width of face bounding box
        h: Height of face bounding box
        confidence: Detection confidence score
    
    Returns:
        FaceDetection object
    """
    facial_area = {'x': x, 'y': y, 'w': w, 'h': h}
    return FaceDetection(
        facial_area=facial_area,
        confidence=confidence
    )


def create_mock_detections(num_detections: int = 2) -> List[FaceDetection]:
    """
    Create a list of mock FaceDetection objects.
    
    Args:
        num_detections: Number of detections to create
    
    Returns:
        List of FaceDetection objects
    """
    detections = []
    
    for i in range(num_detections):
        x = 50 + i * 250
        y = 50 + i * 20
        w = 150 + i * 10
        h = 200 + i * 5
        confidence = 0.95 - i * 0.05
        
        detections.append(create_mock_face_detection(x, y, w, h, confidence))
    
    return detections


class TestImageContext:
    """
    Context manager for creating and cleaning up test images.
    
    Usage:
        with TestImageContext() as ctx:
            img_path = ctx.create_image_with_faces(num_faces=2)
            # Use img_path in tests
        # Files are automatically cleaned up
    """
    
    def __init__(self):
        self.temp_files = []
        self.temp_dirs = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Clean up temporary files
        for file_path in self.temp_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
        
        # Clean up temporary directories
        for dir_path in self.temp_dirs:
            if os.path.exists(dir_path):
                try:
                    import shutil
                    shutil.rmtree(dir_path)
                except Exception:
                    pass
    
    def create_image_with_faces(
        self,
        num_faces: int = 2,
        width: int = 640,
        height: int = 480
    ) -> Tuple[str, List[dict]]:
        """
        Create a test image with faces and return the path.
        
        Returns:
            Tuple of (image_path, list of facial_area dicts)
        """
        img, face_areas = create_test_image_with_faces(width, height, num_faces)
        img_path = save_test_image(img)
        self.temp_files.append(img_path)
        return img_path, face_areas
    
    def create_temp_dir(self) -> str:
        """
        Create a temporary directory for testing.
        
        Returns:
            Path to the temporary directory
        """
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def create_simple_image(
        self,
        width: int = 640,
        height: int = 480,
        color: Tuple[int, int, int] = (255, 255, 255)
    ) -> str:
        """
        Create a simple solid-color test image.
        
        Returns:
            Path to the created image
        """
        img = create_test_image(width, height, 3, color)
        img_path = save_test_image(img)
        self.temp_files.append(img_path)
        return img_path
