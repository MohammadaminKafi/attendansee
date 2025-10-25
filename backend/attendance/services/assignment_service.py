"""
Face Assignment Service

This module provides functionality to assign face crops to students using
K-Nearest Neighbors (KNN) with cosine similarity of embeddings.

Independent of core module, designed for backend integration.

Design Patterns:
- Service Layer: High-level operations for face assignment
- Strategy Pattern: Different assignment strategies can be used
- Single Responsibility: Focused on assignment operations
"""

from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import numpy as np


@dataclass
class AssignmentResult:
    """
    Data class representing an assignment result.
    
    Attributes:
        face_crop_id: ID of the face crop
        assigned_student_id: ID of the assigned student (None if no match)
        confidence: Confidence score (similarity) of the assignment
        k_nearest: List of (student_id, similarity) for K nearest neighbors
    """
    face_crop_id: int
    assigned_student_id: Optional[int]
    confidence: float
    k_nearest: List[Tuple[int, float]]


class AssignmentService:
    """
    Service for assigning face crops to students using KNN similarity search.
    
    This service provides functionality to:
    - Find K nearest neighbors using cosine similarity
    - Assign face crops to most similar student
    - Handle threshold-based filtering
    - Support both single and batch assignments
    
    Example:
        >>> service = AssignmentService(k=5, threshold=0.6)
        >>> result = service.assign_crop_to_student(
        ...     crop_embedding=crop_emb,
        ...     student_embeddings=student_embs
        ... )
        >>> print(f"Assigned to student {result.assigned_student_id}")
    """
    
    def __init__(
        self,
        k: int = 5,
        similarity_threshold: float = 0.6,
        vote_threshold: float = 0.5
    ):
        """
        Initialize the assignment service.
        
        Args:
            k: Number of nearest neighbors to consider
            similarity_threshold: Minimum similarity for a match (0-1)
            vote_threshold: Fraction of K neighbors that must agree (0-1)
                Used for majority voting in KNN
        """
        self.k = k
        self.similarity_threshold = similarity_threshold
        self.vote_threshold = vote_threshold
    
    def find_k_nearest(
        self,
        query_embedding: np.ndarray,
        reference_embeddings: List[Tuple[int, np.ndarray]],
        k: Optional[int] = None
    ) -> List[Tuple[int, float]]:
        """
        Find K nearest neighbors using cosine similarity.
        
        Args:
            query_embedding: The embedding to match
            reference_embeddings: List of (student_id, embedding) tuples
            k: Number of neighbors (uses self.k if not provided)
        
        Returns:
            List of (student_id, similarity) tuples, sorted by similarity (descending)
        """
        if not reference_embeddings:
            return []
        
        k = k or self.k
        
        # Calculate similarities
        similarities = []
        
        for student_id, ref_embedding in reference_embeddings:
            if ref_embedding is None:
                continue
            
            similarity = self._cosine_similarity(query_embedding, ref_embedding)
            similarities.append((student_id, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top K
        return similarities[:k]
    
    def assign_by_knn(
        self,
        query_embedding: np.ndarray,
        reference_embeddings: List[Tuple[int, np.ndarray]],
        use_voting: bool = True
    ) -> Tuple[Optional[int], float, List[Tuple[int, float]]]:
        """
        Assign to a student using KNN strategy.
        
        Args:
            query_embedding: The face embedding to assign
            reference_embeddings: List of (student_id, embedding) for known students
            use_voting: If True, use majority voting; otherwise use best match
        
        Returns:
            Tuple of (assigned_student_id, confidence, k_nearest)
            Returns (None, 0.0, []) if no match found
        """
        # Find K nearest neighbors
        k_nearest = self.find_k_nearest(query_embedding, reference_embeddings)
        
        if not k_nearest:
            return None, 0.0, []
        
        if use_voting:
            # Majority voting strategy
            assigned_student, confidence = self._majority_vote(k_nearest)
        else:
            # Best match strategy (1-NN)
            if k_nearest[0][1] >= self.similarity_threshold:
                assigned_student = k_nearest[0][0]
                confidence = k_nearest[0][1]
            else:
                assigned_student = None
                confidence = 0.0
        
        return assigned_student, confidence, k_nearest
    
    def _majority_vote(
        self,
        k_nearest: List[Tuple[int, float]]
    ) -> Tuple[Optional[int], float]:
        """
        Determine assignment using majority voting.
        
        Args:
            k_nearest: List of (student_id, similarity) tuples
        
        Returns:
            Tuple of (assigned_student_id, average_confidence)
        """
        # Filter by similarity threshold
        valid_neighbors = [
            (sid, sim) for sid, sim in k_nearest
            if sim >= self.similarity_threshold
        ]
        
        if not valid_neighbors:
            return None, 0.0
        
        # Count votes for each student
        votes = {}
        similarities = {}
        
        for student_id, similarity in valid_neighbors:
            if student_id not in votes:
                votes[student_id] = 0
                similarities[student_id] = []
            
            votes[student_id] += 1
            similarities[student_id].append(similarity)
        
        # Find student with most votes
        max_votes = max(votes.values())
        vote_fraction = max_votes / len(valid_neighbors)
        
        # Check if vote threshold is met
        if vote_fraction < self.vote_threshold:
            return None, 0.0
        
        # Get students with max votes
        candidates = [sid for sid, v in votes.items() if v == max_votes]
        
        # If tie, use student with highest average similarity
        if len(candidates) > 1:
            avg_similarities = {
                sid: np.mean(similarities[sid])
                for sid in candidates
            }
            assigned_student = max(avg_similarities, key=avg_similarities.get)
        else:
            assigned_student = candidates[0]
        
        # Calculate average confidence
        confidence = np.mean(similarities[assigned_student])
        
        return assigned_student, float(confidence)
    
    @staticmethod
    def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(vec1, vec2) / (norm1 * norm2))


class FaceCropAssignmentService:
    """
    High-level service for assigning FaceCrop objects to Students.
    
    This service integrates with Django models to:
    - Generate embeddings for face crops if not available
    - Find similar face crops from identified students
    - Assign face crops using KNN similarity
    - Support batch assignment for entire classes
    
    Example:
        >>> service = FaceCropAssignmentService()
        >>> result = service.assign_crop(crop_id=123, k=5)
        >>> if result['assigned']:
        ...     print(f"Assigned to {result['student_name']}")
    """
    
    def __init__(
        self,
        embedding_model: str = 'facenet',
        k: int = 5,
        similarity_threshold: float = 0.6,
        use_voting: bool = True
    ):
        """
        Initialize the face crop assignment service.
        
        Args:
            embedding_model: Model to use for embeddings ('facenet' or 'arcface')
            k: Number of nearest neighbors
            similarity_threshold: Minimum similarity threshold
            use_voting: Whether to use majority voting in KNN
        """
        self.embedding_model = embedding_model
        self.k = k
        self.similarity_threshold = similarity_threshold
        self.use_voting = use_voting
    
    def assign_crop(
        self,
        crop_id: int,
        auto_commit: bool = True
    ) -> Dict[str, Any]:
        """
        Assign a single face crop to a student using KNN.
        
        Args:
            crop_id: ID of the FaceCrop to assign
            auto_commit: Whether to save the assignment to database
        
        Returns:
            Dictionary with assignment results
        """
        from attendance.models import FaceCrop, Student
        from attendance.services import EmbeddingService
        
        # Get the face crop
        try:
            crop = FaceCrop.objects.select_related(
                'image__session__class_session'
            ).get(id=crop_id)
        except FaceCrop.DoesNotExist:
            raise ValueError(f"FaceCrop with ID {crop_id} not found")
        
        # Check if already identified
        if crop.is_identified:
            return {
                'status': 'already_identified',
                'crop_id': crop_id,
                'student_id': crop.student.id if crop.student else None,
                'student_name': crop.student.full_name if crop.student else None,
                'message': 'Face crop is already identified'
            }
        
        # Generate embedding if not available
        embedding_service = EmbeddingService(model_name=self.embedding_model)
        
        if crop.embedding is None or crop.embedding_model != self.embedding_model:
            try:
                crop_path = crop.crop_image_path.path
                embedding_obj = embedding_service.generate_embedding(crop_path)
                crop.embedding = embedding_obj.vector.tolist()
                crop.embedding_model = self.embedding_model
                crop.save(update_fields=['embedding', 'embedding_model', 'updated_at'])
                query_embedding = embedding_obj.vector
            except Exception as e:
                return {
                    'status': 'embedding_failed',
                    'crop_id': crop_id,
                    'error': str(e),
                    'message': 'Failed to generate embedding'
                }
        else:
            query_embedding = np.array(crop.embedding)
        
        # Get all identified face crops from students in the same class
        class_obj = crop.image.session.class_session
        
        identified_crops = FaceCrop.objects.filter(
            image__session__class_session=class_obj,
            is_identified=True,
            student__isnull=False,
            embedding__isnull=False,
            embedding_model=self.embedding_model
        ).select_related('student').exclude(id=crop_id)
        
        if not identified_crops.exists():
            return {
                'status': 'no_reference_data',
                'crop_id': crop_id,
                'message': 'No identified face crops with embeddings found in class'
            }
        
        # Build reference embeddings (student_id -> embeddings list)
        student_embeddings_dict = {}
        
        for ref_crop in identified_crops:
            student_id = ref_crop.student.id
            embedding = np.array(ref_crop.embedding)
            
            if student_id not in student_embeddings_dict:
                student_embeddings_dict[student_id] = []
            
            student_embeddings_dict[student_id].append(embedding)
        
        # Calculate average embedding for each student
        reference_embeddings = []
        for student_id, embeddings in student_embeddings_dict.items():
            avg_embedding = np.mean(embeddings, axis=0)
            reference_embeddings.append((student_id, avg_embedding))
        
        # Perform KNN assignment
        assignment_service = AssignmentService(
            k=self.k,
            similarity_threshold=self.similarity_threshold
        )
        
        assigned_student_id, confidence, k_nearest = assignment_service.assign_by_knn(
            query_embedding=query_embedding,
            reference_embeddings=reference_embeddings,
            use_voting=self.use_voting
        )
        
        # Update database if assigned and auto_commit is True
        if assigned_student_id is not None and auto_commit:
            try:
                student = Student.objects.get(id=assigned_student_id)
                crop.identify_student(student, confidence=confidence)
                
                return {
                    'status': 'assigned',
                    'crop_id': crop_id,
                    'student_id': assigned_student_id,
                    'student_name': student.full_name,
                    'confidence': float(confidence),
                    'k_nearest': [
                        {
                            'student_id': sid,
                            'student_name': Student.objects.get(id=sid).full_name,
                            'similarity': float(sim)
                        }
                        for sid, sim in k_nearest[:self.k]
                    ],
                    'message': 'Face crop assigned successfully'
                }
            except Student.DoesNotExist:
                return {
                    'status': 'student_not_found',
                    'crop_id': crop_id,
                    'error': f"Student with ID {assigned_student_id} not found"
                }
        elif assigned_student_id is not None:
            # Return result without committing
            student = Student.objects.get(id=assigned_student_id)
            return {
                'status': 'match_found',
                'crop_id': crop_id,
                'student_id': assigned_student_id,
                'student_name': student.full_name,
                'confidence': float(confidence),
                'k_nearest': [
                    {
                        'student_id': sid,
                        'student_name': Student.objects.get(id=sid).full_name,
                        'similarity': float(sim)
                    }
                    for sid, sim in k_nearest[:self.k]
                ],
                'message': 'Match found but not committed'
            }
        else:
            return {
                'status': 'no_match',
                'crop_id': crop_id,
                'confidence': 0.0,
                'k_nearest': [
                    {
                        'student_id': sid,
                        'student_name': Student.objects.get(id=sid).full_name,
                        'similarity': float(sim)
                    }
                    for sid, sim in k_nearest[:self.k]
                ] if k_nearest else [],
                'message': 'No matching student found above threshold'
            }
    
    def assign_session_crops(
        self,
        session_id: int,
        auto_commit: bool = True
    ) -> Dict[str, Any]:
        """
        Assign all unidentified face crops in a session to students.
        
        Args:
            session_id: ID of the session
            auto_commit: Whether to save assignments to database
        
        Returns:
            Dictionary with batch assignment results
        """
        from attendance.models import Session, FaceCrop
        
        # Get session
        try:
            session = Session.objects.get(id=session_id)
        except Session.DoesNotExist:
            raise ValueError(f"Session with ID {session_id} not found")
        
        # Get unidentified crops in session
        unidentified_crops = FaceCrop.objects.filter(
            image__session=session,
            is_identified=False
        )
        
        if not unidentified_crops.exists():
            return {
                'status': 'no_unidentified_crops',
                'session_id': session_id,
                'message': 'No unidentified face crops found in session'
            }
        
        # Assign each crop
        results = []
        assigned_count = 0
        no_match_count = 0
        error_count = 0
        
        for crop in unidentified_crops:
            try:
                result = self.assign_crop(crop.id, auto_commit=auto_commit)
                results.append(result)
                
                if result['status'] == 'assigned':
                    assigned_count += 1
                elif result['status'] == 'no_match':
                    no_match_count += 1
                else:
                    error_count += 1
            except Exception as e:
                results.append({
                    'status': 'error',
                    'crop_id': crop.id,
                    'error': str(e)
                })
                error_count += 1
        
        return {
            'status': 'completed',
            'session_id': session_id,
            'session_name': session.name,
            'total_crops': len(results),
            'assigned': assigned_count,
            'no_match': no_match_count,
            'errors': error_count,
            'results': results,
            'parameters': {
                'k': self.k,
                'similarity_threshold': self.similarity_threshold,
                'use_voting': self.use_voting,
                'embedding_model': self.embedding_model
            }
        }
    
    def assign_class_crops(
        self,
        class_id: int,
        auto_commit: bool = True
    ) -> Dict[str, Any]:
        """
        Assign all unidentified face crops in a class to students.
        
        Args:
            class_id: ID of the class
            auto_commit: Whether to save assignments to database
        
        Returns:
            Dictionary with batch assignment results
        """
        from attendance.models import Class, FaceCrop
        
        # Get class
        try:
            class_obj = Class.objects.get(id=class_id)
        except Class.DoesNotExist:
            raise ValueError(f"Class with ID {class_id} not found")
        
        # Get unidentified crops in class
        unidentified_crops = FaceCrop.objects.filter(
            image__session__class_session=class_obj,
            is_identified=False
        )
        
        if not unidentified_crops.exists():
            return {
                'status': 'no_unidentified_crops',
                'class_id': class_id,
                'message': 'No unidentified face crops found in class'
            }
        
        # Assign each crop
        results = []
        assigned_count = 0
        no_match_count = 0
        error_count = 0
        
        for crop in unidentified_crops:
            try:
                result = self.assign_crop(crop.id, auto_commit=auto_commit)
                results.append(result)
                
                if result['status'] == 'assigned':
                    assigned_count += 1
                elif result['status'] == 'no_match':
                    no_match_count += 1
                else:
                    error_count += 1
            except Exception as e:
                results.append({
                    'status': 'error',
                    'crop_id': crop.id,
                    'error': str(e)
                })
                error_count += 1
        
        return {
            'status': 'completed',
            'class_id': class_id,
            'class_name': class_obj.name,
            'total_crops': len(results),
            'assigned': assigned_count,
            'no_match': no_match_count,
            'errors': error_count,
            'results': results,
            'parameters': {
                'k': self.k,
                'similarity_threshold': self.similarity_threshold,
                'use_voting': self.use_voting,
                'embedding_model': self.embedding_model
            }
        }
