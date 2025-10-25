"""
Simple embedding service for generating face embeddings using DeepFace.

Supports multiple models: ArcFace, Facenet, Facenet512
"""
from deepface import DeepFace
from typing import Optional, List
import os


class EmbeddingService:
    """
    Service for generating face embeddings using DeepFace.
    """
    
    # Supported models and their embedding dimensions
    SUPPORTED_MODELS = {
        'arcface': 512,
        'facenet': 128,
        'facenet512': 512,
    }
    
    @staticmethod
    def generate_embedding(
        image_path: str,
        model_name: str = 'arcface'
    ) -> Optional[List[float]]:
        """
        Generate face embedding for a single face crop image.
        
        Args:
            image_path: Path to the face crop image
            model_name: Model to use for embedding generation
                       ('arcface', 'facenet', or 'facenet512')
        
        Returns:
            List of floats representing the embedding vector, or None if failed
        
        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If model_name is not supported
        """
        # Validate image exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Validate model
        model_name = model_name.lower()
        if model_name not in EmbeddingService.SUPPORTED_MODELS:
            raise ValueError(
                f"Unsupported model: {model_name}. "
                f"Supported models: {list(EmbeddingService.SUPPORTED_MODELS.keys())}"
            )
        
        # Map model names to DeepFace model names
        model_mapping = {
            'arcface': 'ArcFace',
            'facenet': 'Facenet',
            'facenet512': 'Facenet512',
        }
        
        deepface_model_name = model_mapping[model_name]
        
        try:
            # Generate embedding
            result = DeepFace.represent(
                img_path=image_path,
                model_name=deepface_model_name
            )
            
            # DeepFace returns a list of dicts for multiple faces
            # For a face crop, we expect only one face
            if result and len(result) > 0:
                embedding = result[0]['embedding']
                return embedding
            
            return None
            
        except Exception as e:
            raise Exception(f"Failed to generate embedding: {str(e)}")
    
    @staticmethod
    def get_embedding_dimension(model_name: str) -> int:
        """
        Get the embedding dimension for a given model.
        
        Args:
            model_name: Name of the model
        
        Returns:
            Embedding dimension (number of features)
        """
        model_name = model_name.lower()
        return EmbeddingService.SUPPORTED_MODELS.get(model_name, 512)
