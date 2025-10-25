"""
Simplified Face Embedding Service

This module provides face embedding generation using DeepFace models.
Designed for simplicity, reliability, and clear error reporting.

DESIGN PRINCIPLES:
1. Subprocess isolation for all embeddings (no direct TensorFlow usage)
2. No caching or threading (each request is independent)
3. Clear error reporting with debugging information
4. Support for FaceNet (128D) and ArcFace (512D) models

ARCHITECTURE:
- Main service runs in Django process
- Embedding generation runs in separate subprocess
- Communication via JSON files
- Complete process isolation prevents memory corruption

KEY SIMPLIFICATIONS:
- Removed threading locks (not needed with subprocess)
- Removed model caching (subprocess is fresh each time)
- Removed fallback mechanisms (subprocess is the only way)
- Removed complex environment management (handled in worker)
"""

import os
import sys
import subprocess
import tempfile
import json
import logging
import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import numpy as np


logger = logging.getLogger(__name__)


@dataclass
class FaceEmbedding:
    """
    Face embedding data structure.
    
    Attributes:
        vector: Embedding vector as numpy array
        model_name: Model used to generate the embedding
        dimension: Dimension of the embedding
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
        
        Raises:
            ValueError: If dimensions don't match
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


class EmbeddingService:
    """
    Simplified service for generating face embeddings.
    
    All embedding generation is done in subprocess for complete isolation.
    This prevents TensorFlow memory corruption from affecting Django.
    
    Supported models:
    - facenet: FaceNet model (128 dimensions)
    - arcface: ArcFace model (512 dimensions)
    
    Example:
        >>> service = EmbeddingService(model_name='facenet')
        >>> embedding = service.generate_embedding('/path/to/face.jpg')
        >>> print(f"Generated {embedding.dimension}D embedding")
    """
    
    # Model configurations
    MODEL_CONFIGS = {
        'facenet': {
            'deepface_name': 'Facenet',
            'dimensions': 128,
            'description': 'FaceNet model (128D)'
        },
        'arcface': {
            'deepface_name': 'ArcFace',
            'dimensions': 512,
            'description': 'ArcFace model (512D)'
        }
    }
    
    # Subprocess timeout in seconds
    SUBPROCESS_TIMEOUT = 120
    
    def __init__(self, model_name: str = 'facenet'):
        """
        Initialize the embedding service.
        
        Args:
            model_name: Model to use ('facenet' or 'arcface')
        
        Raises:
            ValueError: If model name is not supported
        """
        model_name = model_name.lower()
        
        if model_name not in self.MODEL_CONFIGS:
            raise ValueError(
                f"Unsupported model: {model_name}. "
                f"Supported models: {', '.join(self.MODEL_CONFIGS.keys())}"
            )
        
        self.model_name = model_name
        self.config = self.MODEL_CONFIGS[model_name]
        
        logger.info(f"Initialized EmbeddingService with {self.config['description']}")
    
    def generate_embedding(self, image_path: str) -> FaceEmbedding:
        """
        Generate face embedding from an image file.
        
        This method runs embedding generation in a subprocess for complete
        isolation from the Django process. This prevents TensorFlow memory
        corruption issues.
        
        Args:
            image_path: Path to the face crop image
        
        Returns:
            FaceEmbedding object containing the embedding vector
        
        Raises:
            FileNotFoundError: If image doesn't exist
            ValueError: If embedding generation fails
            RuntimeError: If subprocess fails
        """
        # Validate input
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        logger.info(f"Generating {self.model_name} embedding for: {image_path}")
        
        # Generate embedding in subprocess
        result = self._generate_embedding_subprocess(image_path)
        
        # Create FaceEmbedding object
        embedding = FaceEmbedding(
            vector=np.array(result['embedding'], dtype=np.float32),
            model_name=self.model_name
        )
        
        # Verify dimensions
        expected_dim = self.config['dimensions']
        if embedding.dimension != expected_dim:
            raise ValueError(
                f"Expected {expected_dim} dimensions, got {embedding.dimension}"
            )
        
        logger.info(f"Successfully generated {embedding.dimension}D embedding")
        
        return embedding
    
    def _generate_embedding_subprocess(self, image_path: str) -> Dict[str, Any]:
        """
        Generate embedding in a subprocess.
        
        This is the core method that runs the worker script in complete isolation.
        
        Args:
            image_path: Path to face image
        
        Returns:
            Dictionary with embedding data
        
        Raises:
            RuntimeError: If subprocess fails
            ValueError: If embedding generation fails
        """
        # Create temporary file for result
        result_fd, result_file = tempfile.mkstemp(suffix='.json', text=True)
        os.close(result_fd)  # Close file descriptor, worker will open by path
        
        try:
            # Get path to worker script
            worker_script = os.path.join(
                os.path.dirname(__file__),
                'generate_embedding_worker.py'
            )
            
            if not os.path.exists(worker_script):
                raise RuntimeError(f"Worker script not found: {worker_script}")
            
            logger.debug(f"Worker script: {worker_script}")
            logger.debug(f"Result file: {result_file}")
            logger.debug(f"Model: {self.config['deepface_name']}")
            
            # Prepare subprocess command
            cmd = [
                sys.executable,
                worker_script,
                image_path,
                self.config['deepface_name'],
                result_file
            ]
            
            logger.debug(f"Running command: {' '.join(cmd)}")
            
            # Run subprocess
            start_time = time.time()
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = process.communicate(timeout=self.SUBPROCESS_TIMEOUT)
                returncode = process.returncode
                elapsed = time.time() - start_time
                
                logger.debug(f"Subprocess completed in {elapsed:.2f}s with code {returncode}")
                
            except subprocess.TimeoutExpired:
                process.kill()
                elapsed = time.time() - start_time
                logger.error(f"Subprocess timed out after {elapsed:.2f}s")
                raise RuntimeError(
                    f"Embedding generation timed out after {self.SUBPROCESS_TIMEOUT}s"
                )
            
            # Log subprocess output
            if stdout:
                stdout_text = stdout.decode('utf-8', errors='ignore').strip()
                if stdout_text:
                    logger.debug(f"Subprocess stdout:\n{stdout_text}")
            
            if stderr:
                stderr_text = stderr.decode('utf-8', errors='ignore').strip()
                if stderr_text:
                    # Filter out TensorFlow info messages
                    lines = stderr_text.split('\n')
                    filtered_lines = [
                        line for line in lines
                        if not any(skip in line for skip in [
                            'Could not find cuda',
                            'TensorFlow binary is optimized',
                            'I tensorflow',
                            'I external'
                        ])
                    ]
                    
                    if filtered_lines:
                        logger.debug(f"Subprocess stderr:\n{chr(10).join(filtered_lines)}")
            
            # Check if subprocess failed
            if returncode != 0:
                error_msg = f"Subprocess exited with code {returncode}"
                if stderr:
                    error_msg += f"\nStderr: {stderr.decode('utf-8', errors='ignore')[:500]}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            # Read result file
            if not os.path.exists(result_file):
                raise RuntimeError("Subprocess did not create result file")
            
            file_size = os.path.getsize(result_file)
            if file_size == 0:
                raise RuntimeError("Subprocess created empty result file")
            
            logger.debug(f"Reading result file ({file_size} bytes)")
            
            with open(result_file, 'r') as f:
                result = json.load(f)
            
            # Check if generation was successful
            if not result.get('success', False):
                error_msg = result.get('error', 'Unknown error')
                error_type = result.get('error_type', 'Error')
                error_trace = result.get('traceback', 'No traceback available')
                
                logger.error(f"Subprocess embedding generation failed: {error_msg}")
                logger.error(f"Error type: {error_type}")
                logger.debug(f"Traceback:\n{error_trace}")
                
                raise ValueError(f"{error_type}: {error_msg}")
            
            # Validate result
            if 'embedding' not in result:
                raise ValueError("Result missing 'embedding' field")
            
            embedding_list = result['embedding']
            if not isinstance(embedding_list, list) or len(embedding_list) == 0:
                raise ValueError("Invalid embedding format")
            
            logger.debug(f"Successfully loaded {len(embedding_list)}D embedding")
            
            return result
            
        finally:
            # Clean up temporary file
            try:
                if os.path.exists(result_file):
                    os.unlink(result_file)
            except Exception as e:
                logger.warning(f"Failed to clean up temp file: {e}")
    
    def generate_embeddings_batch(
        self,
        image_paths: List[str]
    ) -> List[Optional[FaceEmbedding]]:
        """
        Generate embeddings for multiple images.
        
        Note: Each embedding is generated in a separate subprocess,
        so this is not truly batched, but it's convenient for processing
        multiple images at once.
        
        Args:
            image_paths: List of paths to face crop images
        
        Returns:
            List of FaceEmbedding objects (None for failed images)
        """
        embeddings = []
        
        for idx, image_path in enumerate(image_paths):
            logger.info(f"Processing image {idx + 1}/{len(image_paths)}: {image_path}")
            
            try:
                embedding = self.generate_embedding(image_path)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Failed to generate embedding for {image_path}: {e}")
                embeddings.append(None)
        
        success_count = sum(1 for e in embeddings if e is not None)
        logger.info(f"Batch complete: {success_count}/{len(image_paths)} successful")
        
        return embeddings
    
    @staticmethod
    def calculate_similarity(
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
    
    @staticmethod
    def calculate_distance(
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
    
    @staticmethod
    def cosine_similarity_np(
        vector1: np.ndarray,
        vector2: np.ndarray
    ) -> float:
        """
        Calculate cosine similarity between two vectors.
        
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


# Legacy compatibility - keep old class names

class EmbeddingModelFactory:
    """
    Factory for creating embedding service instances.
    
    Kept for backward compatibility.
    """
    
    @classmethod
    def create(cls, model_name: str) -> EmbeddingService:
        """
        Create an embedding service instance.
        
        Args:
            model_name: Name of the model ('facenet' or 'arcface')
        
        Returns:
            EmbeddingService instance
        """
        return EmbeddingService(model_name=model_name)
    
    @classmethod
    def get_supported_models(cls) -> List[str]:
        """Get list of supported model names."""
        return list(EmbeddingService.MODEL_CONFIGS.keys())
