"""
Tests for the Embedding Service

This module tests the face embedding generation functionality.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from attendance.services.embedding_service import (
    FaceEmbedding,
    FaceNetModel,
    ArcFaceModel,
    EmbeddingModelFactory,
    EmbeddingService,
    generate_embedding,
    calculate_similarity
)


class TestFaceEmbedding:
    """Test the FaceEmbedding data class."""
    
    def test_create_embedding(self):
        """Test creating a face embedding."""
        vector = np.random.rand(128).astype(np.float32)
        embedding = FaceEmbedding(vector=vector, model_name='facenet')
        
        assert embedding.model_name == 'facenet'
        assert embedding.dimension == 128
        assert isinstance(embedding.vector, np.ndarray)
    
    def test_to_list(self):
        """Test converting embedding to list."""
        vector = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        embedding = FaceEmbedding(vector=vector, model_name='facenet')
        
        result = embedding.to_list()
        assert isinstance(result, list)
        assert len(result) == 3
    
    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        vec1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vec2 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        
        emb1 = FaceEmbedding(vector=vec1, model_name='facenet')
        emb2 = FaceEmbedding(vector=vec2, model_name='facenet')
        
        similarity = emb1.cosine_similarity(emb2)
        assert 0.99 < similarity <= 1.0  # Should be very close to 1.0
    
    def test_cosine_distance(self):
        """Test cosine distance calculation."""
        vec1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vec2 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        
        emb1 = FaceEmbedding(vector=vec1, model_name='facenet')
        emb2 = FaceEmbedding(vector=vec2, model_name='facenet')
        
        distance = emb1.cosine_distance(emb2)
        assert 0.0 <= distance < 0.01  # Should be very close to 0.0


class TestEmbeddingModelFactory:
    """Test the embedding model factory."""
    
    def test_create_facenet_model(self):
        """Test creating FaceNet model."""
        model = EmbeddingModelFactory.create('facenet')
        assert isinstance(model, FaceNetModel)
        assert model.get_dimension() == 128
        assert model.get_name() == 'facenet'
    
    def test_create_arcface_model(self):
        """Test creating ArcFace model."""
        model = EmbeddingModelFactory.create('arcface')
        assert isinstance(model, ArcFaceModel)
        assert model.get_dimension() == 512
        assert model.get_name() == 'arcface'
    
    def test_create_invalid_model(self):
        """Test creating invalid model raises error."""
        with pytest.raises(ValueError, match="Unsupported model"):
            EmbeddingModelFactory.create('invalid_model')
    
    def test_get_supported_models(self):
        """Test getting list of supported models."""
        models = EmbeddingModelFactory.get_supported_models()
        assert 'facenet' in models
        assert 'arcface' in models
        assert len(models) >= 2


@pytest.mark.django_db
class TestFaceNetModel:
    """Test the FaceNet embedding model."""
    
    def test_model_properties(self):
        """Test FaceNet model properties."""
        model = FaceNetModel()
        assert model.get_dimension() == 128
        assert model.get_name() == 'facenet'
    
    def test_generate_missing_file(self):
        """Test generating embedding for missing file raises error."""
        model = FaceNetModel()
        with pytest.raises(FileNotFoundError):
            model.generate('/nonexistent/file.jpg')
    
    @patch('deepface.DeepFace')
    def test_generate_embedding_success(self, mock_deepface):
        """Test successful embedding generation."""
        # Mock DeepFace.represent to return a valid embedding
        mock_embedding = np.random.rand(128).astype(np.float32)
        mock_deepface.represent.return_value = [{
            'embedding': mock_embedding.tolist()
        }]
        
        model = FaceNetModel()
        
        # Mock file existence
        with patch('os.path.exists', return_value=True):
            embedding = model.generate('/fake/path.jpg')
        
        assert isinstance(embedding, np.ndarray)
        assert len(embedding) == 128
        mock_deepface.represent.assert_called_once()


@pytest.mark.django_db
class TestArcFaceModel:
    """Test the ArcFace embedding model."""
    
    def test_model_properties(self):
        """Test ArcFace model properties."""
        model = ArcFaceModel()
        assert model.get_dimension() == 512
        assert model.get_name() == 'arcface'
    
    def test_generate_missing_file(self):
        """Test generating embedding for missing file raises error."""
        model = ArcFaceModel()
        with pytest.raises(FileNotFoundError):
            model.generate('/nonexistent/file.jpg')


@pytest.mark.django_db
class TestEmbeddingService:
    """Test the main embedding service."""
    
    def test_init_with_valid_model(self):
        """Test initializing service with valid model."""
        service = EmbeddingService(model_name='facenet')
        assert service.model_name == 'facenet'
        assert isinstance(service.model, FaceNetModel)
    
    def test_init_with_invalid_model(self):
        """Test initializing service with invalid model raises error."""
        with pytest.raises(ValueError):
            EmbeddingService(model_name='invalid')
    
    @patch('deepface.DeepFace')
    def test_generate_embedding(self, mock_deepface):
        """Test generating embedding."""
        mock_embedding = np.random.rand(128).astype(np.float32)
        mock_deepface.represent.return_value = [{
            'embedding': mock_embedding.tolist()
        }]
        
        service = EmbeddingService(model_name='facenet')
        
        with patch('os.path.exists', return_value=True):
            embedding = service.generate_embedding('/fake/path.jpg')
        
        assert isinstance(embedding, FaceEmbedding)
        assert embedding.dimension == 128
        assert embedding.model_name == 'facenet'
    
    def test_calculate_similarity(self):
        """Test calculating similarity between embeddings."""
        vec1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vec2 = np.array([0.8, 0.6, 0.0], dtype=np.float32)
        
        emb1 = FaceEmbedding(vector=vec1, model_name='facenet')
        emb2 = FaceEmbedding(vector=vec2, model_name='facenet')
        
        service = EmbeddingService()
        similarity = service.calculate_similarity(emb1, emb2)
        
        assert 0.0 <= similarity <= 1.0
        assert similarity > 0.5  # Should be somewhat similar
    
    def test_find_best_match(self):
        """Test finding best matching embedding."""
        query = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        query_emb = FaceEmbedding(vector=query, model_name='facenet')
        
        candidates = [
            FaceEmbedding(
                vector=np.array([0.9, 0.1, 0.0], dtype=np.float32),
                model_name='facenet'
            ),
            FaceEmbedding(
                vector=np.array([0.0, 1.0, 0.0], dtype=np.float32),
                model_name='facenet'
            ),
            FaceEmbedding(
                vector=np.array([0.95, 0.05, 0.0], dtype=np.float32),
                model_name='facenet'
            ),
        ]
        
        service = EmbeddingService()
        best_idx, similarity = service.find_best_match(query_emb, candidates)
        
        # Should match the third one (index 2) as it's most similar
        assert best_idx == 2
        assert similarity > 0.9
    
    def test_find_best_match_with_threshold(self):
        """Test finding best match with threshold."""
        query = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        query_emb = FaceEmbedding(vector=query, model_name='facenet')
        
        # Create a dissimilar candidate
        candidates = [
            FaceEmbedding(
                vector=np.array([0.0, 1.0, 0.0], dtype=np.float32),
                model_name='facenet'
            ),
        ]
        
        service = EmbeddingService()
        best_idx, similarity = service.find_best_match(
            query_emb, candidates, threshold=0.8
        )
        
        # Should return no match (-1) as similarity is below threshold
        assert best_idx == -1
        assert similarity == 0.0
    
    def test_find_top_k_matches(self):
        """Test finding top K matches."""
        query = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        query_emb = FaceEmbedding(vector=query, model_name='facenet')
        
        candidates = [
            FaceEmbedding(
                vector=np.array([0.9, 0.1, 0.0], dtype=np.float32),
                model_name='facenet'
            ),
            FaceEmbedding(
                vector=np.array([0.0, 1.0, 0.0], dtype=np.float32),
                model_name='facenet'
            ),
            FaceEmbedding(
                vector=np.array([0.95, 0.05, 0.0], dtype=np.float32),
                model_name='facenet'
            ),
        ]
        
        service = EmbeddingService()
        top_matches = service.find_top_k_matches(query_emb, candidates, k=2)
        
        assert len(top_matches) == 2
        # Results should be sorted by similarity (descending)
        assert top_matches[0][1] >= top_matches[1][1]
    
    def test_cosine_similarity_static(self):
        """Test static cosine similarity method."""
        vec1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vec2 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        
        similarity = EmbeddingService.cosine_similarity_np(vec1, vec2)
        assert 0.99 < similarity <= 1.0
    
    def test_cosine_distance_static(self):
        """Test static cosine distance method."""
        vec1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vec2 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        
        distance = EmbeddingService.cosine_distance_np(vec1, vec2)
        assert 0.0 <= distance < 0.01


@pytest.mark.django_db
class TestConvenienceFunctions:
    """Test convenience functions."""
    
    @patch('deepface.DeepFace')
    def test_generate_embedding_function(self, mock_deepface):
        """Test generate_embedding convenience function."""
        mock_embedding = np.random.rand(128).astype(np.float32)
        mock_deepface.represent.return_value = [{
            'embedding': mock_embedding.tolist()
        }]
        
        with patch('os.path.exists', return_value=True):
            embedding = generate_embedding('/fake/path.jpg', model_name='facenet')
        
        assert isinstance(embedding, FaceEmbedding)
        assert embedding.dimension == 128
    
    @patch('deepface.DeepFace')
    def test_calculate_similarity_function(self, mock_deepface):
        """Test calculate_similarity convenience function."""
        mock_embedding = np.random.rand(128).astype(np.float32)
        mock_deepface.represent.return_value = [{
            'embedding': mock_embedding.tolist()
        }]
        
        with patch('os.path.exists', return_value=True):
            similarity = calculate_similarity(
                '/fake/path1.jpg',
                '/fake/path2.jpg',
                model_name='facenet'
            )
        
        assert isinstance(similarity, float)
        assert 0.0 <= similarity <= 1.0
