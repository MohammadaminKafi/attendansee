"""
Face Embedding Service

This module provides face embedding generation using deep learning models.
Supports multiple embedding models (FaceNet, ArcFace) with a strategy pattern.

This service is independent of the core module but maintains similar design patterns.
Inspired by core/face/aggregator.py but designed specifically for backend integration.

Design Patterns:
- Strategy Pattern: Different embedding models can be swapped
- Factory Pattern: EmbeddingModelFactory creates appropriate model instances
- Single Responsibility: Focused on embedding generation and similarity
"""

from typing import List, Optional, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass
import numpy as np
import os


@dataclass
class FaceEmbedding:
    """
    Data class representing a face embedding.
    
    Attributes:
        vector: The embedding vector as numpy array
        model_name: Name of the model used to generate embedding
        dimension: Dimension of the embedding vector
    """
    vector: np.ndarray
    model_name: str
    
    @property
    def dimension(self) -> int:
        """Get the dimension of the embedding vector."""
        return len(self.vector)
    
    def to_list(self) -> List[float]:
        """Convert embedding vector to Python list."""
        return self.vector.tolist()
    
    def cosine_similarity(self, other: 'FaceEmbedding') -> float:
        """
        Calculate cosine similarity with another embedding.
        
        Args:
            other: Another FaceEmbedding instance
        
        Returns:
            Similarity score (0-1, higher is more similar)
        """
        if self.vector.shape != other.vector.shape:
            raise ValueError(
                f"Embedding dimensions don't match: {self.vector.shape} vs {other.vector.shape}"
            )
        
        # Normalize vectors
        a = self.vector / (np.linalg.norm(self.vector) + 1e-10)
        b = other.vector / (np.linalg.norm(other.vector) + 1e-10)
        
        # Calculate cosine similarity
        similarity = np.dot(a, b)
        
        return float(similarity)
    
    def cosine_distance(self, other: 'FaceEmbedding') -> float:
        """
        Calculate cosine distance with another embedding.
        
        Args:
            other: Another FaceEmbedding instance
        
        Returns:
            Distance score (0-2, lower is more similar)
        """
        return 1.0 - self.cosine_similarity(other)


class EmbeddingModel(ABC):
    """
    Abstract base class for face embedding models.
    
    This defines the interface that all embedding models must implement,
    enabling the strategy pattern for model selection.
    """
    
    @abstractmethod
    def generate(self, image_path: str) -> np.ndarray:
        """
        Generate face embedding from an image.
        
        Args:
            image_path: Path to the face image file
        
        Returns:
            Embedding vector as numpy array
        
        Raises:
            FileNotFoundError: If image doesn't exist
            ValueError: If embedding generation fails
        """
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get the name identifier for this model."""
        pass


class FaceNetModel(EmbeddingModel):
    """
    FaceNet embedding model (128 dimensions).
    
    Uses DeepFace with Facenet model backend.
    """
    
    def __init__(self):
        """Initialize FaceNet model."""
        self._model_name = 'Facenet'
        self._dimension = 128
    
    def generate(self, image_path: str) -> np.ndarray:
        """
        Generate FaceNet embedding from a face image.
        
        Args:
            image_path: Path to face crop image
        
        Returns:
            128-dimensional embedding vector
        
        Raises:
            FileNotFoundError: If image doesn't exist
            ValueError: If embedding generation fails
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        try:
            from deepface import DeepFace
            
            # Generate embedding using DeepFace
            result = DeepFace.represent(
                img_path=image_path,
                model_name=self._model_name,
                enforce_detection=False,
                detector_backend='skip'  # Skip detection, we already have crops
            )
            
            # DeepFace returns list or dict depending on version
            if isinstance(result, list) and len(result) > 0:
                result = result[0]
            
            if isinstance(result, dict) and 'embedding' in result:
                embedding = np.array(result['embedding'], dtype=np.float32)
            elif isinstance(result, (list, tuple)):
                embedding = np.array(result, dtype=np.float32)
            else:
                embedding = np.array(result, dtype=np.float32)
            
            # Ensure correct dimension
            if len(embedding) != self._dimension:
                raise ValueError(
                    f"Expected {self._dimension} dimensions, got {len(embedding)}"
                )
            
            return embedding
        
        except ImportError as e:
            raise RuntimeError(
                "DeepFace not installed. Install with: pip install deepface"
            ) from e
        except Exception as e:
            raise ValueError(f"Failed to generate FaceNet embedding: {str(e)}") from e
    
    def get_dimension(self) -> int:
        """Get embedding dimension (128)."""
        return self._dimension
    
    def get_name(self) -> str:
        """Get model name identifier."""
        return 'facenet'


class ArcFaceModel(EmbeddingModel):
    """
    ArcFace embedding model (512 dimensions).
    
    Uses DeepFace with ArcFace model backend.
    """
    
    def __init__(self):
        """Initialize ArcFace model."""
        self._model_name = 'ArcFace'
        self._dimension = 512
    
    def generate(self, image_path: str) -> np.ndarray:
        """
        Generate ArcFace embedding from a face image.
        
        Args:
            image_path: Path to face crop image
        
        Returns:
            512-dimensional embedding vector
        
        Raises:
            FileNotFoundError: If image doesn't exist
            ValueError: If embedding generation fails
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        try:
            from deepface import DeepFace
            
            # Generate embedding using DeepFace
            result = DeepFace.represent(
                img_path=image_path,
                model_name=self._model_name,
                enforce_detection=False,
                detector_backend='skip'  # Skip detection, we already have crops
            )
            
            # DeepFace returns list or dict depending on version
            if isinstance(result, list) and len(result) > 0:
                result = result[0]
            
            if isinstance(result, dict) and 'embedding' in result:
                embedding = np.array(result['embedding'], dtype=np.float32)
            elif isinstance(result, (list, tuple)):
                embedding = np.array(result, dtype=np.float32)
            else:
                embedding = np.array(result, dtype=np.float32)
            
            # Ensure correct dimension
            if len(embedding) != self._dimension:
                raise ValueError(
                    f"Expected {self._dimension} dimensions, got {len(embedding)}"
                )
            
            return embedding
        
        except ImportError as e:
            raise RuntimeError(
                "DeepFace not installed. Install with: pip install deepface"
            ) from e
        except Exception as e:
            raise ValueError(f"Failed to generate ArcFace embedding: {str(e)}") from e
    
    def get_dimension(self) -> int:
        """Get embedding dimension (512)."""
        return self._dimension
    
    def get_name(self) -> str:
        """Get model name identifier."""
        return 'arcface'


class EmbeddingModelFactory:
    """
    Factory for creating embedding model instances.
    
    Supports:
    - facenet: FaceNet model (128D)
    - arcface: ArcFace model (512D)
    """
    
    _models = {
        'facenet': FaceNetModel,
        'arcface': ArcFaceModel,
    }
    
    @classmethod
    def create(cls, model_name: str) -> EmbeddingModel:
        """
        Create an embedding model instance.
        
        Args:
            model_name: Name of the model ('facenet' or 'arcface')
        
        Returns:
            EmbeddingModel instance
        
        Raises:
            ValueError: If model name is not supported
        """
        model_name = model_name.lower()
        
        if model_name not in cls._models:
            raise ValueError(
                f"Unsupported model: {model_name}. "
                f"Supported models: {', '.join(cls._models.keys())}"
            )
        
        return cls._models[model_name]()
    
    @classmethod
    def get_supported_models(cls) -> List[str]:
        """Get list of supported model names."""
        return list(cls._models.keys())


class EmbeddingService:
    """
    Service for generating and comparing face embeddings.
    
    This is the main service class for working with face embeddings.
    It provides high-level operations for:
    - Generating embeddings from face images
    - Calculating similarities between embeddings
    - Finding best matches from a set of embeddings
    
    Example:
        >>> service = EmbeddingService(model_name='facenet')
        >>> embedding = service.generate_embedding('/path/to/face.jpg')
        >>> print(f"Generated {embedding.dimension}D embedding")
        
        >>> # Compare with another face
        >>> other_embedding = service.generate_embedding('/path/to/other_face.jpg')
        >>> similarity = embedding.cosine_similarity(other_embedding)
        >>> print(f"Similarity: {similarity:.2f}")
    """
    
    def __init__(self, model_name: str = 'facenet'):
        """
        Initialize the embedding service.
        
        Args:
            model_name: Name of the embedding model to use
                Options: 'facenet' (128D), 'arcface' (512D)
        
        Raises:
            ValueError: If model name is not supported
        """
        self.model = EmbeddingModelFactory.create(model_name)
        self.model_name = model_name
    
    def generate_embedding(self, image_path: str) -> FaceEmbedding:
        """
        Generate face embedding from an image file.
        
        Args:
            image_path: Path to the face crop image
        
        Returns:
            FaceEmbedding object containing the embedding vector
        
        Raises:
            FileNotFoundError: If image doesn't exist
            ValueError: If embedding generation fails
        """
        vector = self.model.generate(image_path)
        
        return FaceEmbedding(
            vector=vector,
            model_name=self.model.get_name()
        )
    
    def generate_embeddings_batch(
        self,
        image_paths: List[str]
    ) -> List[Optional[FaceEmbedding]]:
        """
        Generate embeddings for multiple images.
        
        Args:
            image_paths: List of paths to face crop images
        
        Returns:
            List of FaceEmbedding objects (None for failed images)
        """
        embeddings = []
        
        for image_path in image_paths:
            try:
                embedding = self.generate_embedding(image_path)
                embeddings.append(embedding)
            except Exception:
                # Skip failed embeddings but maintain order
                embeddings.append(None)
        
        return embeddings
    
    def calculate_similarity(
        self,
        embedding1: FaceEmbedding,
        embedding2: FaceEmbedding
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
        
        Returns:
            Similarity score (0-1, higher is more similar)
        """
        return embedding1.cosine_similarity(embedding2)
    
    def calculate_distance(
        self,
        embedding1: FaceEmbedding,
        embedding2: FaceEmbedding
    ) -> float:
        """
        Calculate cosine distance between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
        
        Returns:
            Distance score (0-2, lower is more similar)
        """
        return embedding1.cosine_distance(embedding2)
    
    def find_best_match(
        self,
        query_embedding: FaceEmbedding,
        candidate_embeddings: List[FaceEmbedding],
        threshold: Optional[float] = None
    ) -> Tuple[int, float]:
        """
        Find the best matching embedding from a list of candidates.
        
        Args:
            query_embedding: The embedding to match
            candidate_embeddings: List of candidate embeddings
            threshold: Optional similarity threshold (0-1)
                If provided, only matches above threshold are considered
        
        Returns:
            Tuple of (best_index, similarity_score)
            Returns (-1, 0.0) if no match found or below threshold
        """
        if not candidate_embeddings:
            return -1, 0.0
        
        best_idx = -1
        best_similarity = 0.0
        
        for idx, candidate in enumerate(candidate_embeddings):
            if candidate is None:
                continue
            
            similarity = self.calculate_similarity(query_embedding, candidate)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_idx = idx
        
        # Check threshold
        if threshold is not None and best_similarity < threshold:
            return -1, 0.0
        
        return best_idx, best_similarity
    
    def find_top_k_matches(
        self,
        query_embedding: FaceEmbedding,
        candidate_embeddings: List[FaceEmbedding],
        k: int = 5,
        threshold: Optional[float] = None
    ) -> List[Tuple[int, float]]:
        """
        Find the top K best matching embeddings.
        
        Args:
            query_embedding: The embedding to match
            candidate_embeddings: List of candidate embeddings
            k: Number of top matches to return
            threshold: Optional similarity threshold
        
        Returns:
            List of (index, similarity) tuples, sorted by similarity (descending)
        """
        if not candidate_embeddings:
            return []
        
        # Calculate similarities
        similarities = []
        for idx, candidate in enumerate(candidate_embeddings):
            if candidate is None:
                continue
            
            similarity = self.calculate_similarity(query_embedding, candidate)
            
            # Apply threshold if provided
            if threshold is None or similarity >= threshold:
                similarities.append((idx, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top K
        return similarities[:k]
    
    @staticmethod
    def cosine_similarity_np(
        vector1: np.ndarray,
        vector2: np.ndarray
    ) -> float:
        """
        Static method to calculate cosine similarity between two vectors.
        
        Args:
            vector1: First embedding vector
            vector2: Second embedding vector
        
        Returns:
            Similarity score (0-1)
        """
        # Normalize vectors
        a = vector1 / (np.linalg.norm(vector1) + 1e-10)
        b = vector2 / (np.linalg.norm(vector2) + 1e-10)
        
        # Calculate cosine similarity
        return float(np.dot(a, b))
    
    @staticmethod
    def cosine_distance_np(
        vector1: np.ndarray,
        vector2: np.ndarray
    ) -> float:
        """
        Static method to calculate cosine distance between two vectors.
        
        Args:
            vector1: First embedding vector
            vector2: Second embedding vector
        
        Returns:
            Distance score (0-2)
        """
        return 1.0 - EmbeddingService.cosine_similarity_np(vector1, vector2)


# Convenience functions for direct usage
def generate_embedding(
    image_path: str,
    model_name: str = 'facenet'
) -> FaceEmbedding:
    """
    Convenience function to generate a face embedding.
    
    Args:
        image_path: Path to face image
        model_name: Model to use ('facenet' or 'arcface')
    
    Returns:
        FaceEmbedding object
    """
    service = EmbeddingService(model_name=model_name)
    return service.generate_embedding(image_path)


def calculate_similarity(
    image_path1: str,
    image_path2: str,
    model_name: str = 'facenet'
) -> float:
    """
    Convenience function to calculate similarity between two face images.
    
    Args:
        image_path1: Path to first face image
        image_path2: Path to second face image
        model_name: Model to use ('facenet' or 'arcface')
    
    Returns:
        Similarity score (0-1)
    """
    service = EmbeddingService(model_name=model_name)
    emb1 = service.generate_embedding(image_path1)
    emb2 = service.generate_embedding(image_path2)
    return service.calculate_similarity(emb1, emb2)
