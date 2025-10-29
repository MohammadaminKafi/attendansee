"""
Embedding service for generating face embeddings using DeepFace.

Clean, maintainable design with a small strategy/factory pattern so adding
new models later is straightforward.

Supported models (512D only):
- arcface      -> DeepFace model 'ArcFace'
- facenet512   -> DeepFace model 'Facenet512'
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Type

from deepface import DeepFace


class EmbeddingModel(ABC):
    """Abstract embedding model contract."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Short lowercase name used across the app (e.g., 'arcface')."""
        raise NotImplementedError

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding vector dimension for this model."""
        raise NotImplementedError

    @property
    @abstractmethod
    def deepface_name(self) -> str:
        """Corresponding model name in DeepFace (e.g., 'ArcFace')."""
        raise NotImplementedError

    def represent(self, image_path: str) -> Optional[List[float]]:
        """Generate the embedding using DeepFace and normalize the output."""
        result = DeepFace.represent(img_path=image_path, model_name=self.deepface_name)
        # DeepFace returns List[Dict] when enforce_detection=False and multiple faces
        if result and isinstance(result, list):
            first = result[0]
            if isinstance(first, dict) and 'embedding' in first:
                return first['embedding']
        return None


class ArcFaceModel(EmbeddingModel):
    @property
    def name(self) -> str:
        return 'arcface'

    @property
    def dimension(self) -> int:
        return 512

    @property
    def deepface_name(self) -> str:
        return 'ArcFace'


class FaceNet512Model(EmbeddingModel):
    @property
    def name(self) -> str:
        return 'facenet512'

    @property
    def dimension(self) -> int:
        return 512

    @property
    def deepface_name(self) -> str:
        return 'Facenet512'


class EmbeddingModelFactory:
    """Factory for creating embedding model instances by name."""

    _registry: Dict[str, Type[EmbeddingModel]] = {
        'arcface': ArcFaceModel,
        'facenet512': FaceNet512Model,
    }

    @classmethod
    def create(cls, model_name: str) -> EmbeddingModel:
        key = (model_name or '').lower()
        if key not in cls._registry:
            raise ValueError(
                f"Unsupported model: {model_name}. Supported models: {list(cls._registry.keys())}"
            )
        return cls._registry[key]()

    @classmethod
    def supported_models(cls) -> Dict[str, int]:
        return {name: impl().dimension for name, impl in cls._registry.items()}


class EmbeddingService:
    """
    Service for generating face embeddings using a pluggable model backend.
    
    Usage patterns:
    - Static one-shot call: EmbeddingService.generate_embedding(path, 'arcface')
    - Instance for repeated calls with same model:
        service = EmbeddingService(model_name='arcface')
        emb = service.generate(image_path)
    """

    def __init__(self, model_name: str = 'arcface') -> None:
        self.model = EmbeddingModelFactory.create(model_name)

    def generate(self, image_path: str) -> Optional[List[float]]:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        return self.model.represent(image_path)

    # Backwards-compatible static API used by views
    @staticmethod
    def generate_embedding(image_path: str, model_name: str = 'arcface') -> Optional[List[float]]:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        model = EmbeddingModelFactory.create(model_name)
        return model.represent(image_path)

    @staticmethod
    def get_embedding_dimension(model_name: str) -> int:
        key = (model_name or '').lower()
        return EmbeddingModelFactory.supported_models().get(key, 512)

    @staticmethod
    def supported_models() -> Dict[str, int]:
        """Expose supported models and their dimensions to callers/UI."""
        return EmbeddingModelFactory.supported_models()
