"""
Services package for attendance application.

This package contains business logic services that handle:
- Face detection and recognition
- Image processing and manipulation
- Face embedding generation
- Face crop clustering
- PDF report generation
"""

from .face_detection import FaceDetectionService
from .image_processor import ImageProcessor
from .embedding_service import EmbeddingService
from .assignment_service import AssignmentService
from .clustering_service import ClusteringService
from .pdf_service import BasePDFService, AttendancePDFService

__all__ = [
    'FaceDetectionService',
    'ImageProcessor',
    'EmbeddingService',
    'AssignmentService',
    'ClusteringService',
    'BasePDFService',
    'AttendancePDFService',
]
