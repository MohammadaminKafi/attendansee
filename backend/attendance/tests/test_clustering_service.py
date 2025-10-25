"""
Tests for the Clustering Service

This module tests the face crop clustering functionality.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from attendance.services.clustering_service import (
    ClusterResult,
    ClusteringService,
    FaceCropClusteringService
)


class TestClusterResult:
    """Test the ClusterResult data class."""
    
    def test_create_cluster_result(self):
        """Test creating a cluster result."""
        labels = np.array([0, 0, 1, 1, 2])
        result = ClusterResult(
            cluster_labels=labels,
            num_clusters=3,
            cluster_sizes={0: 2, 1: 2, 2: 1}
        )
        
        assert result.num_clusters == 3
        assert len(result.cluster_labels) == 5
    
    def test_get_cluster_members(self):
        """Test getting members of a cluster."""
        labels = np.array([0, 0, 1, 1, 2])
        result = ClusterResult(
            cluster_labels=labels,
            num_clusters=3
        )
        
        members = result.get_cluster_members(0)
        assert members == [0, 1]
        
        members = result.get_cluster_members(1)
        assert members == [2, 3]
    
    def test_get_all_clusters(self):
        """Test getting all clusters."""
        labels = np.array([0, 0, 1, 1, 2])
        result = ClusterResult(
            cluster_labels=labels,
            num_clusters=3
        )
        
        clusters = result.get_all_clusters()
        assert len(clusters) == 3
        assert clusters[0] == [0, 1]
        assert clusters[1] == [2, 3]
        assert clusters[2] == [4]


class TestClusteringService:
    """Test the clustering service."""
    
    def test_init(self):
        """Test initializing clustering service."""
        service = ClusteringService(
            max_clusters=20,
            similarity_threshold=0.6
        )
        assert service.max_clusters == 20
        assert service.similarity_threshold == 0.6
    
    def test_cluster_single_embedding(self):
        """Test clustering with single embedding."""
        embeddings = [np.random.rand(128).astype(np.float32)]
        service = ClusteringService()
        
        result = service.cluster_embeddings(embeddings)
        
        assert result.num_clusters == 1
        assert len(result.cluster_labels) == 1
        assert result.cluster_labels[0] == 0
    
    def test_cluster_empty_embeddings(self):
        """Test clustering with empty embeddings raises error."""
        service = ClusteringService()
        
        with pytest.raises(ValueError, match="Embeddings list cannot be empty"):
            service.cluster_embeddings([])
    
    @patch('sklearn.cluster.AgglomerativeClustering')
    @patch('sklearn.metrics.pairwise.cosine_similarity')
    def test_cluster_multiple_embeddings(self, mock_cosine, mock_clustering):
        """Test clustering multiple embeddings."""
        # Create similar embeddings for two groups
        embeddings = [
            np.array([1.0, 0.0, 0.0], dtype=np.float32),
            np.array([0.9, 0.1, 0.0], dtype=np.float32),
            np.array([0.0, 1.0, 0.0], dtype=np.float32),
            np.array([0.0, 0.9, 0.1], dtype=np.float32),
        ]
        
        # Mock similarity matrix
        mock_cosine.return_value = np.array([
            [1.0, 0.95, 0.0, 0.0],
            [0.95, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.95],
            [0.0, 0.0, 0.95, 1.0],
        ])
        
        # Mock clustering result
        mock_cluster_instance = MagicMock()
        mock_cluster_instance.fit_predict.return_value = np.array([0, 0, 1, 1])
        mock_clustering.return_value = mock_cluster_instance
        
        service = ClusteringService(similarity_threshold=0.6)
        result = service.cluster_embeddings(embeddings)
        
        assert result.num_clusters == 2
        assert len(result.cluster_labels) == 4
    
    def test_assign_to_existing_clusters(self):
        """Test assigning new embeddings to existing clusters."""
        # Create cluster centers
        cluster_centers = [
            np.array([1.0, 0.0, 0.0], dtype=np.float32),
            np.array([0.0, 1.0, 0.0], dtype=np.float32),
        ]
        
        # Create new embeddings similar to first cluster
        new_embeddings = [
            np.array([0.95, 0.05, 0.0], dtype=np.float32),
            np.array([0.0, 0.95, 0.05], dtype=np.float32),
        ]
        
        service = ClusteringService(similarity_threshold=0.7)
        assignments = service.assign_to_existing_clusters(
            new_embeddings, cluster_centers
        )
        
        assert len(assignments) == 2
        assert assignments[0] == 0  # Should assign to first cluster
        assert assignments[1] == 1  # Should assign to second cluster


@pytest.mark.django_db
class TestFaceCropClusteringService:
    """Test the face crop clustering service with Django models."""
    
    def test_init(self):
        """Test initializing face crop clustering service."""
        service = FaceCropClusteringService(
            embedding_model='facenet',
            max_clusters=30,
            similarity_threshold=0.55
        )
        
        assert service.embedding_model == 'facenet'
        assert service.max_clusters == 30
        assert service.similarity_threshold == 0.55
    
    def test_cluster_session_crops_no_session(self):
        """Test clustering with non-existent session raises error."""
        service = FaceCropClusteringService()
        
        with pytest.raises(ValueError, match="Session .* not found"):
            service.cluster_session_crops(session_id=99999)
    
    @pytest.fixture
    def setup_test_data(self, db, django_user_model):
        """Set up test data for clustering tests."""
        from attendance.models import Class, Session, Image, FaceCrop
        from django.utils import timezone
        import tempfile
        from PIL import Image as PILImage
        import os
        
        # Create user
        user = django_user_model.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create class
        class_obj = Class.objects.create(
            owner=user,
            name='Test Class',
            description='Test Description'
        )
        
        # Create session
        session = Session.objects.create(
            class_session=class_obj,
            name='Test Session',
            date=timezone.now().date()
        )
        
        # Create temporary image
        temp_dir = tempfile.mkdtemp()
        img_path = os.path.join(temp_dir, 'test_image.jpg')
        pil_img = PILImage.new('RGB', (100, 100), color='red')
        pil_img.save(img_path)
        
        # Create image
        image = Image.objects.create(
            session=session,
            original_image_path=img_path,
            is_processed=True
        )
        
        # Create face crops
        crops = []
        for i in range(3):
            crop_path = os.path.join(temp_dir, f'crop_{i}.jpg')
            pil_img.save(crop_path)
            
            crop = FaceCrop.objects.create(
                image=image,
                crop_image_path=crop_path,
                coordinates=f'{i*10},{i*10},50,50'
            )
            crops.append(crop)
        
        return {
            'user': user,
            'class': class_obj,
            'session': session,
            'image': image,
            'crops': crops,
            'temp_dir': temp_dir
        }
    
    def test_cluster_session_crops_no_crops(self, setup_test_data):
        """Test clustering session with no face crops."""
        # Create new session without crops
        from attendance.models import Session
        from django.utils import timezone
        
        empty_session = Session.objects.create(
            class_session=setup_test_data['class'],
            name='Empty Session',
            date=timezone.now().date()
        )
        
        service = FaceCropClusteringService()
        result = service.cluster_session_crops(
            session_id=empty_session.id,
            create_students=False
        )
        
        assert result['status'] == 'no_crops'
        assert result['clusters_found'] == 0
    
    @patch('attendance.services.clustering_service.ClusteringService')
    def test_cluster_session_crops_success(
        self, mock_clustering_service_class, setup_test_data
    ):
        """Test successful session crop clustering."""
        # Pre-populate embeddings on crops to avoid mocking embedding generation
        for i, crop in enumerate(setup_test_data['crops']):
            # Create embeddings with slight variations to simulate different faces
            base_embedding = np.random.rand(128).tolist()
            # Pad to 512 dimensions
            embedding_512 = base_embedding + [0.0] * (512 - 128)
            crop.embedding = embedding_512
            crop.embedding_model = 'facenet'
            crop.save()
        
        # Mock clustering
        mock_cluster_instance = MagicMock()
        mock_result = ClusterResult(
            cluster_labels=np.array([0, 0, 1]),
            num_clusters=2,
            cluster_sizes={0: 2, 1: 1}
        )
        mock_cluster_instance.cluster_embeddings.return_value = mock_result
        mock_clustering_service_class.return_value = mock_cluster_instance
        
        service = FaceCropClusteringService()
        result = service.cluster_session_crops(
            session_id=setup_test_data['session'].id,
            create_students=True,
            assign_crops=True
        )
        
        assert result['status'] == 'success'
        assert result['clusters_found'] == 2
