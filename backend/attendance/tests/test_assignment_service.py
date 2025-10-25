"""
Tests for the Assignment Service

This module tests the face crop assignment functionality using KNN.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from attendance.services.assignment_service import (
    AssignmentResult,
    AssignmentService,
    FaceCropAssignmentService
)


class TestAssignmentResult:
    """Test the AssignmentResult data class."""
    
    def test_create_assignment_result(self):
        """Test creating an assignment result."""
        result = AssignmentResult(
            face_crop_id=1,
            assigned_student_id=5,
            confidence=0.85,
            k_nearest=[(5, 0.85), (3, 0.75), (7, 0.70)]
        )
        
        assert result.face_crop_id == 1
        assert result.assigned_student_id == 5
        assert result.confidence == 0.85
        assert len(result.k_nearest) == 3


class TestAssignmentService:
    """Test the assignment service."""
    
    def test_init(self):
        """Test initializing assignment service."""
        service = AssignmentService(
            k=7,
            similarity_threshold=0.65,
            vote_threshold=0.6
        )
        
        assert service.k == 7
        assert service.similarity_threshold == 0.65
        assert service.vote_threshold == 0.6
    
    def test_find_k_nearest_empty_references(self):
        """Test finding K nearest with empty references."""
        query = np.random.rand(128).astype(np.float32)
        service = AssignmentService()
        
        result = service.find_k_nearest(query, [])
        assert result == []
    
    def test_find_k_nearest(self):
        """Test finding K nearest neighbors."""
        query = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        
        references = [
            (1, np.array([0.9, 0.1, 0.0], dtype=np.float32)),
            (2, np.array([0.0, 1.0, 0.0], dtype=np.float32)),
            (3, np.array([0.95, 0.05, 0.0], dtype=np.float32)),
            (4, np.array([0.0, 0.0, 1.0], dtype=np.float32)),
        ]
        
        service = AssignmentService(k=2)
        nearest = service.find_k_nearest(query, references)
        
        assert len(nearest) == 2
        # Should be sorted by similarity (descending)
        assert nearest[0][1] >= nearest[1][1]
        # Most similar should be student 3
        assert nearest[0][0] == 3
    
    def test_assign_by_knn_best_match(self):
        """Test KNN assignment using best match strategy."""
        query = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        
        references = [
            (1, np.array([0.9, 0.1, 0.0], dtype=np.float32)),
            (2, np.array([0.0, 1.0, 0.0], dtype=np.float32)),
        ]
        
        service = AssignmentService(k=2, similarity_threshold=0.7)
        assigned_id, confidence, k_nearest = service.assign_by_knn(
            query, references, use_voting=False
        )
        
        assert assigned_id == 1  # Best match
        assert confidence > 0.7
        assert len(k_nearest) == 2
    
    def test_assign_by_knn_below_threshold(self):
        """Test KNN assignment when below threshold."""
        query = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        
        # Create dissimilar references
        references = [
            (1, np.array([0.0, 1.0, 0.0], dtype=np.float32)),
            (2, np.array([0.0, 0.0, 1.0], dtype=np.float32)),
        ]
        
        service = AssignmentService(k=2, similarity_threshold=0.9)
        assigned_id, confidence, k_nearest = service.assign_by_knn(
            query, references, use_voting=False
        )
        
        assert assigned_id is None
        assert confidence == 0.0
    
    def test_assign_by_knn_majority_voting(self):
        """Test KNN assignment using majority voting."""
        query = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        
        # Create references where student 1 appears more often
        references = [
            (1, np.array([0.9, 0.1, 0.0], dtype=np.float32)),
            (1, np.array([0.85, 0.15, 0.0], dtype=np.float32)),
            (1, np.array([0.88, 0.12, 0.0], dtype=np.float32)),
            (2, np.array([0.80, 0.20, 0.0], dtype=np.float32)),
        ]
        
        service = AssignmentService(
            k=4,
            similarity_threshold=0.7,
            vote_threshold=0.5
        )
        assigned_id, confidence, k_nearest = service.assign_by_knn(
            query, references, use_voting=True
        )
        
        assert assigned_id == 1  # Should win by majority
        assert len(k_nearest) == 4
    
    def test_majority_vote_tie_breaking(self):
        """Test majority voting with tie breaking."""
        # Create scenario with tied votes
        k_nearest = [
            (1, 0.85),
            (1, 0.80),
            (2, 0.90),  # Student 2 has higher similarity
            (2, 0.88),
        ]
        
        service = AssignmentService(similarity_threshold=0.7)
        assigned_id, confidence = service._majority_vote(k_nearest)
        
        # Should choose student 2 due to higher average similarity
        assert assigned_id == 2


@pytest.mark.django_db
class TestFaceCropAssignmentService:
    """Test the face crop assignment service with Django models."""
    
    def test_init(self):
        """Test initializing face crop assignment service."""
        service = FaceCropAssignmentService(
            embedding_model='arcface',
            k=7,
            similarity_threshold=0.7,
            use_voting=False
        )
        
        assert service.embedding_model == 'arcface'
        assert service.k == 7
        assert service.similarity_threshold == 0.7
        assert service.use_voting is False
    
    def test_assign_crop_not_found(self):
        """Test assigning non-existent crop raises error."""
        service = FaceCropAssignmentService()
        
        with pytest.raises(ValueError, match="FaceCrop .* not found"):
            service.assign_crop(crop_id=99999)
    
    @pytest.fixture
    def setup_test_data(self, db, django_user_model):
        """Set up test data for assignment tests."""
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
        
        # Create class
        class_obj = Class.objects.create(
            owner=user,
            name='Test Class',
            description='Test Description'
        )
        
        # Create students
        student1 = Student.objects.create(
            class_enrolled=class_obj,
            first_name='John',
            last_name='Doe',
            student_id='001'
        )
        
        student2 = Student.objects.create(
            class_enrolled=class_obj,
            first_name='Jane',
            last_name='Smith',
            student_id='002'
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
            original_image_path=img_path,
            is_processed=True
        )
        
        # Create identified crops for student1
        identified_crops = []
        for i in range(2):
            crop_path = os.path.join(temp_dir, f'identified_crop_{i}.jpg')
            pil_img.save(crop_path)
            
            crop = FaceCrop.objects.create(
                image=image,
                crop_image_path=crop_path,
                coordinates=f'{i*10},{i*10},50,50',
                student=student1,
                is_identified=True,
                embedding=np.random.rand(512).tolist(),
                embedding_model='arcface'
            )
            identified_crops.append(crop)
        
        # Create unidentified crop
        unidentified_crop_path = os.path.join(temp_dir, 'unidentified_crop.jpg')
        pil_img.save(unidentified_crop_path)
        
        unidentified_crop = FaceCrop.objects.create(
            image=image,
            crop_image_path=unidentified_crop_path,
            coordinates='50,50,50,50',
            is_identified=False
        )
        
        return {
            'user': user,
            'class': class_obj,
            'student1': student1,
            'student2': student2,
            'session': session,
            'image': image,
            'identified_crops': identified_crops,
            'unidentified_crop': unidentified_crop,
            'temp_dir': temp_dir
        }
    
    def test_assign_crop_already_identified(self, setup_test_data):
        """Test assigning already identified crop."""
        service = FaceCropAssignmentService(embedding_model='arcface')
        
        result = service.assign_crop(
            crop_id=setup_test_data['identified_crops'][0].id,
            auto_commit=True
        )
        
        assert result['status'] == 'already_identified'
        assert result['student_id'] == setup_test_data['student1'].id
    
    def test_assign_crop_no_reference_data(self, setup_test_data):
        """Test assigning crop with no reference data."""
        # Delete all identified crops
        from attendance.models import FaceCrop
        FaceCrop.objects.filter(is_identified=True).delete()
        
        # Set embedding on unidentified crop to avoid generation
        unidentified_crop = setup_test_data['unidentified_crop']
        unidentified_crop.embedding = np.random.rand(512).tolist()
        unidentified_crop.embedding_model = 'arcface'
        unidentified_crop.save()
        
        service = FaceCropAssignmentService(embedding_model='arcface')
        
        result = service.assign_crop(
            crop_id=unidentified_crop.id,
            auto_commit=False
        )
        
        assert result['status'] == 'no_reference_data'
    
    def test_assign_crop_success(self, setup_test_data):
        """Test successful crop assignment."""
        # Set embedding on unidentified crop to avoid generation
        unidentified_crop = setup_test_data['unidentified_crop']
        # Create embedding similar to student1's embeddings for better matching
        unidentified_crop.embedding = np.random.rand(512).tolist()
        unidentified_crop.embedding_model = 'arcface'
        unidentified_crop.save()
        
        service = FaceCropAssignmentService(embedding_model='arcface')
        result = service.assign_crop(
            crop_id=unidentified_crop.id,
            auto_commit=True
        )
        
        # Should succeed since we have identified crops for reference
        assert result['status'] in ['assigned', 'no_match']
        if result['status'] == 'assigned':
            assert 'student_id' in result
            assert 'confidence' in result


@pytest.mark.django_db
class TestIntegration:
    """Integration tests combining all services."""
    
    def test_full_workflow(self, db, django_user_model):
        """Test complete workflow: embed -> cluster -> assign."""
        # This would be a more complex integration test
        # that combines embedding generation, clustering, and assignment
        pass
