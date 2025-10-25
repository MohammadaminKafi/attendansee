"""
Services package for attendance application.

This package contains business logic services that handle:
- Face detection and recognition
- Image processing and manipulation
- Face embedding generation
"""

from .face_detection import FaceDetectionService
from .image_processor import ImageProcessor
from .embedding_service import EmbeddingService

__all__ = [
    'FaceDetectionService',
    'ImageProcessor',
    'EmbeddingService',
]
