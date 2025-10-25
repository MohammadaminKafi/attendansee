"""
Tests for New API Endpoints

This module tests the API endpoints for embedding, clustering, and assignment.
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from unittest.mock import patch, MagicMock
import numpy as np


@pytest.mark.django_db
class TestEmbeddingEndpoints:
    """Test embedding generation endpoints."""
    
    @pytest.fixture
    def setup(self, db, django_user_model):
        """Set up test data."""
        from attendance.models import Class, Session, Image, FaceCrop
        from django.utils import timezone
        import tempfile
        from PIL import Image as PILImage
        import os
        
        # Create user and authenticate
        user = django_user_model.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Create class
        class_obj = Class.objects.create(
            owner=user,
            name='Test Class'
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
            original_image_path=img_path
        )
        
        # Create face crop
        crop_path = os.path.join(temp_dir, 'crop.jpg')
        pil_img.save(crop_path)
        
        crop = FaceCrop.objects.create(
            image=image,
            crop_image_path=crop_path,
            coordinates='10,10,50,50'
        )
        
        return {
            'client': client,
            'user': user,
            'class': class_obj,
            'session': session,
            'image': image,
            'crop': crop
        }
    
    def test_generate_embedding_single(self, setup):
        """Test generating embedding for a single face crop."""
        # Pre-set an embedding to test the "already_exists" path
        # Note: Database expects 512 dimensions, pad with zeros for FaceNet
        crop = setup['crop']
        embedding_128 = np.random.rand(128).tolist()
        # Pad to 512 dimensions (database constraint)
        embedding_512 = embedding_128 + [0.0] * (512 - 128)
        crop.embedding = embedding_512
        crop.embedding_model = 'facenet'
        crop.save()
        
        url = reverse('attendance:facecrop-generate-embedding', kwargs={'pk': crop.id})
        response = setup['client'].post(url, {
            'model_name': 'facenet',
            'force_regenerate': False
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'already_exists'
        assert response.data['embedding_model'] == 'facenet'
        assert response.data['embedding_dimension'] == 512
    
    def test_generate_embeddings_batch(self, setup):
        """Test generating embeddings for multiple face crops."""
        # Pre-set an embedding to test the "skipped" path
        # Note: Database expects 512 dimensions, pad with zeros for FaceNet
        crop = setup['crop']
        embedding_128 = np.random.rand(128).tolist()
        # Pad to 512 dimensions (database constraint)
        embedding_512 = embedding_128 + [0.0] * (512 - 128)
        crop.embedding = embedding_512
        crop.embedding_model = 'facenet'
        crop.save()
        
        url = reverse('attendance:facecrop-generate-embeddings-batch')
        response = setup['client'].post(url, {
            'face_crop_ids': [crop.id],
            'model_name': 'facenet',
            'force_regenerate': False
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'completed'
        assert response.data['skipped'] >= 1


@pytest.mark.django_db
class TestClusteringEndpoints:
    """Test clustering endpoints."""
    
    @pytest.fixture
    def setup(self, db, django_user_model):
        """Set up test data."""
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
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Create class
        class_obj = Class.objects.create(
            owner=user,
            name='Test Class'
        )
        
        # Create session
        session = Session.objects.create(
            class_session=class_obj,
            name='Test Session',
            date=timezone.now().date()
        )
        
        # Create temporary images
        temp_dir = tempfile.mkdtemp()
        img_path = os.path.join(temp_dir, 'test_image.jpg')
        pil_img = PILImage.new('RGB', (100, 100), color='red')
        pil_img.save(img_path)
        
        # Create image
        image = Image.objects.create(
            session=session,
            original_image_path=img_path
        )
        
        # Create multiple face crops
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
            'client': client,
            'user': user,
            'class': class_obj,
            'session': session,
            'image': image,
            'crops': crops
        }
    
    @patch('attendance.services.clustering_service.FaceCropClusteringService.cluster_session_crops')
    def test_cluster_session_crops(self, mock_cluster, setup):
        """Test clustering face crops in a session."""
        # Mock clustering result
        mock_cluster.return_value = {
            'status': 'success',
            'clusters_found': 2,
            'students_created': 2,
            'crops_assigned': 3
        }
        
        url = reverse('attendance:session-cluster-crops', kwargs={'pk': setup['session'].id})
        response = setup['client'].post(url, {
            'max_clusters': 20,
            'similarity_threshold': 0.5,
            'embedding_model': 'facenet',
            'create_students': True,
            'assign_crops': True
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'success'
        assert response.data['clusters_found'] == 2
    
    @patch('attendance.services.clustering_service.FaceCropClusteringService.cluster_class_crops')
    def test_cluster_class_crops(self, mock_cluster, setup):
        """Test clustering face crops in a class."""
        # Mock clustering result
        mock_cluster.return_value = {
            'status': 'success',
            'clusters_found': 3,
            'students_created': 3,
            'crops_assigned': 3
        }
        
        url = reverse('attendance:class-cluster-crops', kwargs={'pk': setup['class'].id})
        response = setup['client'].post(url, {
            'max_clusters': 30,
            'similarity_threshold': 0.5,
            'embedding_model': 'facenet',
            'create_students': True,
            'assign_crops': True,
            'include_identified': False
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'success'


@pytest.mark.django_db
class TestAssignmentEndpoints:
    """Test assignment endpoints."""
    
    @pytest.fixture
    def setup(self, db, django_user_model):
        """Set up test data."""
        from attendance.models import Class, Session, Image, FaceCrop, Student
        from django.utils import timezone
        import tempfile
        from PIL import Image as PILImage
        import os
        
        # Create user
        user = django_user_model.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Create class
        class_obj = Class.objects.create(
            owner=user,
            name='Test Class'
        )
        
        # Create student
        student = Student.objects.create(
            class_enrolled=class_obj,
            first_name='John',
            last_name='Doe',
            student_id='001'
        )
        
        # Create session
        session = Session.objects.create(
            class_session=class_obj,
            name='Test Session',
            date=timezone.now().date()
        )
        
        # Create temporary images
        temp_dir = tempfile.mkdtemp()
        img_path = os.path.join(temp_dir, 'test_image.jpg')
        pil_img = PILImage.new('RGB', (100, 100), color='red')
        pil_img.save(img_path)
        
        # Create image
        image = Image.objects.create(
            session=session,
            original_image_path=img_path
        )
        
        # Create unidentified crop
        crop_path = os.path.join(temp_dir, 'crop.jpg')
        pil_img.save(crop_path)
        
        crop = FaceCrop.objects.create(
            image=image,
            crop_image_path=crop_path,
            coordinates='10,10,50,50',
            is_identified=False
        )
        
        return {
            'client': client,
            'user': user,
            'class': class_obj,
            'student': student,
            'session': session,
            'image': image,
            'crop': crop
        }
    
    @patch('attendance.services.assignment_service.FaceCropAssignmentService.assign_crop')
    def test_assign_single_crop(self, mock_assign, setup):
        """Test assigning a single face crop to a student."""
        # Mock assignment result
        mock_assign.return_value = {
            'status': 'assigned',
            'crop_id': setup['crop'].id,
            'student_id': setup['student'].id,
            'student_name': 'John Doe',
            'confidence': 0.85,
            'k_nearest': []
        }
        
        # URL name is based on method name, not url_path
        url = reverse('attendance:facecrop-assign-crop', kwargs={'pk': setup['crop'].id})
        response = setup['client'].post(url, {
            'k': 5,
            'similarity_threshold': 0.6,
            'embedding_model': 'facenet',
            'use_voting': True,
            'auto_commit': True
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'assigned'
        assert response.data['confidence'] == 0.85
    
    @patch('attendance.services.assignment_service.FaceCropAssignmentService.assign_session_crops')
    def test_assign_session_crops(self, mock_assign, setup):
        """Test batch assignment for a session."""
        # Mock assignment result
        mock_assign.return_value = {
            'status': 'completed',
            'session_id': setup['session'].id,
            'total_crops': 1,
            'assigned': 1,
            'no_match': 0,
            'errors': 0
        }
        
        # URL name is based on method name (assign_crops_batch), not url_path
        url = reverse('attendance:session-assign-crops-batch', kwargs={'pk': setup['session'].id})
        response = setup['client'].post(url, {
            'k': 5,
            'similarity_threshold': 0.6,
            'embedding_model': 'facenet',
            'use_voting': True,
            'auto_commit': True
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'completed'
        assert response.data['assigned'] == 1
    
    @patch('attendance.services.assignment_service.FaceCropAssignmentService.assign_class_crops')
    def test_assign_class_crops(self, mock_assign, setup):
        """Test batch assignment for a class."""
        # Mock assignment result
        mock_assign.return_value = {
            'status': 'completed',
            'class_id': setup['class'].id,
            'total_crops': 1,
            'assigned': 1,
            'no_match': 0,
            'errors': 0
        }
        
        # URL name is based on method name (assign_crops_batch), not url_path
        url = reverse('attendance:class-assign-crops-batch', kwargs={'pk': setup['class'].id})
        response = setup['client'].post(url, {
            'k': 5,
            'similarity_threshold': 0.6,
            'embedding_model': 'facenet',
            'use_voting': True,
            'auto_commit': True
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'completed'


@pytest.mark.django_db
class TestPermissions:
    """Test API permissions for new endpoints."""
    
    def test_unauthenticated_access(self, db):
        """Test that unauthenticated users cannot access endpoints."""
        client = APIClient()
        
        # Test embedding endpoint
        url = reverse('attendance:facecrop-generate-embedding', kwargs={'pk': 1})
        response = client.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test clustering endpoint
        url = reverse('attendance:session-cluster-crops', kwargs={'pk': 1})
        response = client.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test assignment endpoint (URL name is based on method name)
        url = reverse('attendance:facecrop-assign-crop', kwargs={'pk': 1})
        response = client.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
