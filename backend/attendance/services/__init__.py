"""
Services package for attendance application.

This package contains business logic services that handle:
- Face detection and recognition
- Image processing and manipulation
- Face embedding generation and similarity
- Face clustering and grouping
- Face crop assignment to students
- Data aggregation and analytics
"""

from .face_detection import FaceDetectionService
from .image_processor import ImageProcessor
from .embedding_service import (
    EmbeddingService,
    FaceEmbedding,
    EmbeddingModelFactory,
    generate_embedding,
    calculate_similarity
)
from .clustering_service import (
    ClusteringService,
    FaceCropClusteringService,
    ClusterResult
)
from .assignment_service import (
    AssignmentService,
    FaceCropAssignmentService,
    AssignmentResult
)

__all__ = [
    'FaceDetectionService',
    'ImageProcessor',
    'EmbeddingService',
    'FaceEmbedding',
    'EmbeddingModelFactory',
    'generate_embedding',
    'calculate_similarity',
    'ClusteringService',
    'FaceCropClusteringService',
    'ClusterResult',
    'AssignmentService',
    'FaceCropAssignmentService',
    'AssignmentResult',
]
