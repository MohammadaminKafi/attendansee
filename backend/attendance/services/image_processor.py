"""
Image Processor Service

This module handles image manipulation operations including:
- Drawing rectangles over detected faces
- Applying grayscale and shadow effects to non-face regions
- Saving processed images

Design Patterns:
- Strategy Pattern: Different processing strategies can be applied
- Builder Pattern: Complex image processing can be built step by step
- Single Responsibility: Focused on image manipulation only
"""

from typing import List, Tuple, Optional
import os
import numpy as np


class ImageProcessor:
    """
    Service for processing images with face detection overlays.
    
    This service provides functionality to:
    - Draw rectangles around detected faces
    - Apply grayscale/shadow effects to non-face regions
    - Create visually enhanced attendance images
    
    Example:
        >>> processor = ImageProcessor()
        >>> processor.load_image('/path/to/image.jpg')
        >>> processor.draw_face_rectangles(detections)
        >>> processor.apply_background_effect()
        >>> processor.save('/path/to/output.jpg')
    """
    
    def __init__(
        self,
        rectangle_color: Tuple[int, int, int] = (0, 255, 0),
        rectangle_thickness: int = 2,
        background_alpha: float = 0.6,
        background_gray_strength: float = 0.7
    ):
        """
        Initialize the image processor.
        
        Args:
            rectangle_color: BGR color for face rectangles (default: green)
            rectangle_thickness: Thickness of rectangle lines in pixels
            background_alpha: Alpha blending for background effect (0-1)
                0 = fully original, 1 = fully processed
            background_gray_strength: Strength of grayscale effect (0-1)
                0 = no grayscale, 1 = full grayscale
        """
        self.rectangle_color = rectangle_color
        self.rectangle_thickness = rectangle_thickness
        self.background_alpha = background_alpha
        self.background_gray_strength = background_gray_strength
        
        self._image = None
        self._original_image = None
        self._mask = None
    
    def load_image(self, image_path: str) -> 'ImageProcessor':
        """
        Load an image from file.
        
        Args:
            image_path: Path to the image file
        
        Returns:
            Self for method chaining
        
        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If image cannot be loaded
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        try:
            import cv2
            
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            self._image = image.copy()
            self._original_image = image.copy()
            
            # Initialize mask (all background initially)
            self._mask = np.zeros(image.shape[:2], dtype=np.uint8)
            
            return self
        
        except ImportError as e:
            raise RuntimeError(
                "OpenCV not installed. Please install it with: pip install opencv-python"
            ) from e
    
    def load_from_array(self, image_array: np.ndarray) -> 'ImageProcessor':
        """
        Load an image from a numpy array.
        
        Args:
            image_array: Numpy array representing the image
        
        Returns:
            Self for method chaining
        
        Raises:
            ValueError: If array is invalid
        """
        if not isinstance(image_array, np.ndarray):
            raise ValueError("Image array must be a numpy ndarray")
        
        if len(image_array.shape) not in [2, 3]:
            raise ValueError("Image array must be 2D (grayscale) or 3D (color)")
        
        self._image = image_array.copy()
        self._original_image = image_array.copy()
        self._mask = np.zeros(image_array.shape[:2], dtype=np.uint8)
        
        return self
    
    def draw_face_rectangles(
        self,
        detections: List,
        color: Optional[Tuple[int, int, int]] = None,
        thickness: Optional[int] = None
    ) -> 'ImageProcessor':
        """
        Draw rectangles around detected faces.
        
        Args:
            detections: List of FaceDetection objects or dicts with facial_area
            color: Optional override for rectangle color
            thickness: Optional override for rectangle thickness
        
        Returns:
            Self for method chaining
        
        Raises:
            ValueError: If no image is loaded
        """
        if self._image is None:
            raise ValueError("No image loaded. Call load_image() first.")
        
        try:
            import cv2
            
            rect_color = color or self.rectangle_color
            rect_thickness = thickness or self.rectangle_thickness
            
            for detection in detections:
                # Get facial area coordinates
                if hasattr(detection, 'facial_area'):
                    facial_area = detection.facial_area
                elif isinstance(detection, dict):
                    facial_area = detection.get('facial_area', detection)
                else:
                    continue
                
                x = facial_area.get('x', 0)
                y = facial_area.get('y', 0)
                w = facial_area.get('w', 0)
                h = facial_area.get('h', 0)
                
                # Draw rectangle
                cv2.rectangle(
                    self._image,
                    (x, y),
                    (x + w, y + h),
                    rect_color,
                    rect_thickness
                )
                
                # Update mask to mark this region as "face"
                self._mask[y:y+h, x:x+w] = 255
            
            return self
        
        except ImportError as e:
            raise RuntimeError(
                "OpenCV not installed. Please install it with: pip install opencv-python"
            ) from e
    
    def apply_background_effect(
        self,
        alpha: Optional[float] = None,
        gray_strength: Optional[float] = None
    ) -> 'ImageProcessor':
        """
        Apply grayscale and shadow effects to non-face regions.
        
        This makes faces stand out by making the background darker and grayer.
        
        Args:
            alpha: Optional override for background alpha blending
            gray_strength: Optional override for grayscale strength
        
        Returns:
            Self for method chaining
        
        Raises:
            ValueError: If no image is loaded
        """
        if self._image is None:
            raise ValueError("No image loaded. Call load_image() first.")
        
        try:
            import cv2
            
            alpha_val = alpha if alpha is not None else self.background_alpha
            gray_val = gray_strength if gray_strength is not None else self.background_gray_strength
            
            # Convert original to grayscale
            gray_image = cv2.cvtColor(self._original_image, cv2.COLOR_BGR2GRAY)
            gray_image_bgr = cv2.cvtColor(gray_image, cv2.COLOR_GRAY2BGR)
            
            # Blend grayscale with original (controls how gray it becomes)
            background_effect = cv2.addWeighted(
                self._original_image,
                1 - gray_val,
                gray_image_bgr,
                gray_val,
                0
            )
            
            # Darken the background effect
            background_effect = (background_effect * (1 - alpha_val * 0.3)).astype(np.uint8)
            
            # Create 3-channel mask
            mask_3channel = cv2.cvtColor(self._mask, cv2.COLOR_GRAY2BGR)
            
            # Apply effect only to background (where mask is 0)
            # Where mask is 255 (face), keep original image
            # Where mask is 0 (background), apply effect
            result = np.where(
                mask_3channel == 255,
                self._image,  # Keep faces as-is (with rectangles)
                cv2.addWeighted(
                    self._image,
                    1 - alpha_val,
                    background_effect,
                    alpha_val,
                    0
                )
            )
            
            self._image = result.astype(np.uint8)
            
            return self
        
        except ImportError as e:
            raise RuntimeError(
                "OpenCV not installed. Please install it with: pip install opencv-python"
            ) from e
    
    def save(self, output_path: str) -> str:
        """
        Save the processed image to disk.
        
        Args:
            output_path: Path where to save the image
        
        Returns:
            Path to the saved image
        
        Raises:
            ValueError: If no image is loaded or saving fails
        """
        if self._image is None:
            raise ValueError("No image loaded. Call load_image() first.")
        
        try:
            import cv2
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save the image
            success = cv2.imwrite(output_path, self._image)
            
            if not success:
                raise ValueError(f"Failed to save image to {output_path}")
            
            return output_path
        
        except ImportError as e:
            raise RuntimeError(
                "OpenCV not installed. Please install it with: pip install opencv-python"
            ) from e
        except Exception as e:
            raise ValueError(f"Failed to save image: {str(e)}") from e
    
    def get_processed_image(self) -> np.ndarray:
        """
        Get the processed image as a numpy array.
        
        Returns:
            Numpy array of the processed image
        
        Raises:
            ValueError: If no image is loaded
        """
        if self._image is None:
            raise ValueError("No image loaded. Call load_image() first.")
        
        return self._image.copy()
    
    def reset(self) -> 'ImageProcessor':
        """
        Reset to the original loaded image.
        
        Returns:
            Self for method chaining
        
        Raises:
            ValueError: If no image is loaded
        """
        if self._original_image is None:
            raise ValueError("No image loaded. Call load_image() first.")
        
        self._image = self._original_image.copy()
        self._mask = np.zeros(self._original_image.shape[:2], dtype=np.uint8)
        
        return self
    
    @staticmethod
    def process_image_with_faces(
        input_path: str,
        output_path: str,
        detections: List,
        rectangle_color: Tuple[int, int, int] = (0, 255, 0),
        rectangle_thickness: int = 2,
        apply_background: bool = True,
        background_alpha: float = 0.6,
        background_gray_strength: float = 0.7
    ) -> str:
        """
        Convenience method to process an image in one call.
        
        This is a static factory method that creates a processor,
        loads an image, applies all effects, and saves the result.
        
        Args:
            input_path: Path to input image
            output_path: Path to save processed image
            detections: List of face detections
            rectangle_color: Color for face rectangles
            rectangle_thickness: Thickness of rectangles
            apply_background: Whether to apply background effect
            background_alpha: Alpha for background blending
            background_gray_strength: Strength of grayscale effect
        
        Returns:
            Path to the saved processed image
        
        Example:
            >>> ImageProcessor.process_image_with_faces(
            ...     'input.jpg',
            ...     'output.jpg',
            ...     detections
            ... )
        """
        processor = ImageProcessor(
            rectangle_color=rectangle_color,
            rectangle_thickness=rectangle_thickness,
            background_alpha=background_alpha,
            background_gray_strength=background_gray_strength
        )
        
        processor.load_image(input_path)
        processor.draw_face_rectangles(detections)
        
        if apply_background:
            processor.apply_background_effect()
        
        return processor.save(output_path)
