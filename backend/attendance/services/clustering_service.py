"""
Face Clustering Service

This module provides clustering functionality for grouping similar face crops.
Uses embeddings to cluster faces and can create student records for each cluster.

Independent of core module but maintains similar design patterns.
Inspired by core/face/aggregator.py clustering logic.

Design Patterns:
- Strategy Pattern: Different clustering algorithms can be used
- Service Layer: High-level operations for face clustering
- Single Responsibility: Focused on clustering operations
"""

from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import numpy as np


@dataclass
class ClusterResult:
    """
    Data class representing clustering results.
    
    Attributes:
        cluster_labels: Array of cluster labels for each face
        num_clusters: Number of clusters found
        cluster_centers: Optional center embeddings for each cluster
        cluster_sizes: Number of faces in each cluster
    """
    cluster_labels: np.ndarray
    num_clusters: int
    cluster_centers: Optional[List[np.ndarray]] = None
    cluster_sizes: Optional[Dict[int, int]] = None
    
    def get_cluster_members(self, cluster_id: int) -> List[int]:
        """
        Get indices of all members in a specific cluster.
        
        Args:
            cluster_id: The cluster ID
        
        Returns:
            List of indices belonging to this cluster
        """
        return [i for i, label in enumerate(self.cluster_labels) if label == cluster_id]
    
    def get_all_clusters(self) -> Dict[int, List[int]]:
        """
        Get a dictionary mapping cluster IDs to member indices.
        
        Returns:
            Dictionary of {cluster_id: [member_indices]}
        """
        clusters = {}
        for cluster_id in range(self.num_clusters):
            clusters[cluster_id] = self.get_cluster_members(cluster_id)
        return clusters


class ClusteringService:
    """
    Service for clustering face crops based on their embeddings.
    
    This service provides functionality to:
    - Cluster faces using similarity-based methods
    - Determine optimal number of clusters
    - Handle noise/outliers
    - Create representative embeddings for clusters
    
    Uses agglomerative clustering with distance threshold for flexible clustering.
    
    Example:
        >>> service = ClusteringService(max_clusters=20, similarity_threshold=0.6)
        >>> result = service.cluster_embeddings(embeddings)
        >>> print(f"Found {result.num_clusters} clusters")
    """
    
    def __init__(
        self,
        max_clusters: int = 50,
        similarity_threshold: float = 0.5,
        min_cluster_size: int = 1
    ):
        """
        Initialize the clustering service.
        
        Args:
            max_clusters: Maximum number of clusters to create
            similarity_threshold: Similarity threshold for grouping (0-1)
                Higher threshold = more strict grouping = more clusters
            min_cluster_size: Minimum number of faces per cluster
        """
        self.max_clusters = max_clusters
        self.similarity_threshold = similarity_threshold
        self.min_cluster_size = min_cluster_size
    
    def cluster_embeddings(
        self,
        embeddings: List[np.ndarray]
    ) -> ClusterResult:
        """
        Cluster face embeddings using agglomerative clustering.
        
        Args:
            embeddings: List of embedding vectors (numpy arrays)
        
        Returns:
            ClusterResult with cluster assignments
        
        Raises:
            ValueError: If embeddings list is empty or invalid
        """
        if not embeddings:
            raise ValueError("Embeddings list cannot be empty")
        
        # Filter out None values
        valid_embeddings = [e for e in embeddings if e is not None]
        
        if not valid_embeddings:
            raise ValueError("No valid embeddings provided")
        
        # Convert to numpy array
        embeddings_array = np.array(valid_embeddings)
        
        if len(embeddings_array.shape) != 2:
            raise ValueError("Embeddings must be 2D array")
        
        # Single embedding case
        if len(embeddings_array) == 1:
            return ClusterResult(
                cluster_labels=np.array([0]),
                num_clusters=1,
                cluster_centers=[embeddings_array[0]],
                cluster_sizes={0: 1}
            )
        
        try:
            from sklearn.cluster import AgglomerativeClustering
            from sklearn.metrics.pairwise import cosine_similarity
            
            # Calculate similarity matrix
            similarity_matrix = cosine_similarity(embeddings_array)
            
            # Convert similarity to distance (1 - similarity)
            distance_matrix = 1 - similarity_matrix
            
            # Calculate distance threshold from similarity threshold
            # similarity_threshold=0.6 means distance_threshold=0.4
            distance_threshold = 1 - self.similarity_threshold
            
            # Perform agglomerative clustering
            clustering = AgglomerativeClustering(
                n_clusters=None,  # Let it determine based on threshold
                distance_threshold=distance_threshold,
                metric='precomputed',
                linkage='average'
            )
            
            labels = clustering.fit_predict(distance_matrix)
            
            num_clusters = len(set(labels))
            
            # If we have too many clusters, merge similar ones
            if num_clusters > self.max_clusters:
                labels = self._merge_small_clusters(
                    embeddings_array,
                    labels,
                    self.max_clusters
                )
                num_clusters = len(set(labels))
            
            # Calculate cluster centers
            cluster_centers = []
            cluster_sizes = {}
            
            for cluster_id in range(num_clusters):
                cluster_mask = labels == cluster_id
                cluster_embeddings = embeddings_array[cluster_mask]
                
                # Calculate center as mean of cluster embeddings
                center = np.mean(cluster_embeddings, axis=0)
                cluster_centers.append(center)
                
                cluster_sizes[cluster_id] = int(np.sum(cluster_mask))
            
            return ClusterResult(
                cluster_labels=labels,
                num_clusters=num_clusters,
                cluster_centers=cluster_centers,
                cluster_sizes=cluster_sizes
            )
        
        except ImportError as e:
            raise RuntimeError(
                "scikit-learn not installed. Install with: pip install scikit-learn"
            ) from e
        except Exception as e:
            raise ValueError(f"Clustering failed: {str(e)}") from e
    
    def _merge_small_clusters(
        self,
        embeddings: np.ndarray,
        labels: np.ndarray,
        target_clusters: int
    ) -> np.ndarray:
        """
        Merge small clusters to reach target number of clusters.
        
        Args:
            embeddings: Array of embeddings
            labels: Current cluster labels
            target_clusters: Target number of clusters
        
        Returns:
            Updated cluster labels
        """
        try:
            from sklearn.cluster import AgglomerativeClustering
            
            # Re-cluster with fixed number of clusters
            clustering = AgglomerativeClustering(
                n_clusters=target_clusters,
                metric='cosine',
                linkage='average'
            )
            
            new_labels = clustering.fit_predict(embeddings)
            return new_labels
        
        except Exception:
            # If merging fails, just return original labels
            return labels
    
    def cluster_with_noise_detection(
        self,
        embeddings: List[np.ndarray],
        noise_threshold: float = 0.3
    ) -> Tuple[ClusterResult, List[int]]:
        """
        Cluster embeddings and detect outliers/noise.
        
        Uses DBSCAN to identify noise points that don't fit well into clusters.
        
        Args:
            embeddings: List of embedding vectors
            noise_threshold: Distance threshold for considering a point as noise
        
        Returns:
            Tuple of (ClusterResult, list of noise indices)
        """
        if not embeddings:
            raise ValueError("Embeddings list cannot be empty")
        
        valid_embeddings = [e for e in embeddings if e is not None]
        
        if not valid_embeddings:
            raise ValueError("No valid embeddings provided")
        
        embeddings_array = np.array(valid_embeddings)
        
        try:
            from sklearn.cluster import DBSCAN
            
            # Use DBSCAN for noise detection
            # eps = 1 - similarity (cosine distance)
            eps = 1 - self.similarity_threshold
            
            dbscan = DBSCAN(
                eps=eps,
                min_samples=self.min_cluster_size,
                metric='cosine'
            )
            
            labels = dbscan.fit_predict(embeddings_array)
            
            # Label -1 indicates noise/outliers
            noise_indices = [i for i, label in enumerate(labels) if label == -1]
            
            # Re-label clusters to start from 0 (excluding noise)
            valid_labels = labels[labels != -1]
            
            if len(valid_labels) > 0:
                unique_labels = sorted(set(valid_labels))
                label_mapping = {old: new for new, old in enumerate(unique_labels)}
                
                # Create new labels array
                new_labels = np.array([-1] * len(labels))
                for i, label in enumerate(labels):
                    if label != -1:
                        new_labels[i] = label_mapping[label]
                
                # Get only non-noise embeddings and labels for result
                non_noise_mask = new_labels != -1
                non_noise_embeddings = embeddings_array[non_noise_mask]
                non_noise_labels = new_labels[non_noise_mask]
                
                num_clusters = len(unique_labels)
                
                # Calculate cluster centers
                cluster_centers = []
                cluster_sizes = {}
                
                for cluster_id in range(num_clusters):
                    cluster_mask = non_noise_labels == cluster_id
                    cluster_embeddings = non_noise_embeddings[cluster_mask]
                    
                    center = np.mean(cluster_embeddings, axis=0)
                    cluster_centers.append(center)
                    cluster_sizes[cluster_id] = int(np.sum(cluster_mask))
                
                result = ClusterResult(
                    cluster_labels=non_noise_labels,
                    num_clusters=num_clusters,
                    cluster_centers=cluster_centers,
                    cluster_sizes=cluster_sizes
                )
            else:
                # All points are noise
                result = ClusterResult(
                    cluster_labels=np.array([]),
                    num_clusters=0,
                    cluster_centers=[],
                    cluster_sizes={}
                )
            
            return result, noise_indices
        
        except ImportError as e:
            raise RuntimeError(
                "scikit-learn not installed. Install with: pip install scikit-learn"
            ) from e
        except Exception as e:
            raise ValueError(f"Noise detection clustering failed: {str(e)}") from e
    
    def assign_to_existing_clusters(
        self,
        new_embeddings: List[np.ndarray],
        cluster_centers: List[np.ndarray],
        threshold: Optional[float] = None
    ) -> List[int]:
        """
        Assign new embeddings to existing cluster centers.
        
        Args:
            new_embeddings: List of new embedding vectors to assign
            cluster_centers: List of existing cluster center embeddings
            threshold: Optional similarity threshold for assignment
        
        Returns:
            List of cluster IDs for each new embedding (-1 if no match)
        """
        if not new_embeddings or not cluster_centers:
            return []
        
        threshold = threshold or self.similarity_threshold
        
        assignments = []
        
        for embedding in new_embeddings:
            if embedding is None:
                assignments.append(-1)
                continue
            
            # Find best matching cluster
            best_cluster = -1
            best_similarity = 0.0
            
            for cluster_id, center in enumerate(cluster_centers):
                # Calculate cosine similarity
                similarity = self._cosine_similarity(embedding, center)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_cluster = cluster_id
            
            # Check threshold
            if best_similarity >= threshold:
                assignments.append(best_cluster)
            else:
                assignments.append(-1)  # No match
        
        return assignments
    
    @staticmethod
    def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(vec1, vec2) / (norm1 * norm2))


class FaceCropClusteringService:
    """
    High-level service for clustering FaceCrop objects from the database.
    
    This service integrates with Django models to:
    - Generate embeddings for face crops if not available
    - Cluster face crops within a session or class
    - Create Student records for identified clusters
    - Update FaceCrop records with cluster assignments
    
    Example:
        >>> service = FaceCropClusteringService()
        >>> result = service.cluster_session_crops(
        ...     session_id=123,
        ...     max_clusters=20,
        ...     similarity_threshold=0.6
        ... )
        >>> print(f"Created {result['students_created']} new students")
    """
    
    def __init__(
        self,
        embedding_model: str = 'facenet',
        max_clusters: int = 50,
        similarity_threshold: float = 0.5
    ):
        """
        Initialize the face crop clustering service.
        
        Args:
            embedding_model: Model to use for embeddings ('facenet' or 'arcface')
            max_clusters: Maximum number of clusters
            similarity_threshold: Similarity threshold for grouping
        """
        self.embedding_model = embedding_model
        self.max_clusters = max_clusters
        self.similarity_threshold = similarity_threshold
    
    def cluster_session_crops(
        self,
        session_id: int,
        create_students: bool = True,
        assign_crops: bool = True
    ) -> Dict[str, Any]:
        """
        Cluster all face crops in a session.
        
        Args:
            session_id: ID of the session to cluster
            create_students: Whether to create Student records for clusters
            assign_crops: Whether to assign face crops to created students
        
        Returns:
            Dictionary with clustering results and statistics
        """
        from attendance.models import Session, FaceCrop, Student
        from attendance.services import EmbeddingService
        
        # Get session
        try:
            session = Session.objects.get(id=session_id)
        except Session.DoesNotExist:
            raise ValueError(f"Session with ID {session_id} not found")
        
        # Get all face crops in the session
        face_crops = FaceCrop.objects.filter(
            image__session=session
        ).select_related('image', 'student')
        
        if not face_crops.exists():
            return {
                'status': 'no_crops',
                'message': 'No face crops found in session',
                'clusters_found': 0,
                'students_created': 0,
                'crops_assigned': 0
            }
        
        # Generate embeddings if not available
        embedding_service = EmbeddingService(model_name=self.embedding_model)
        embeddings = []
        crop_list = list(face_crops)
        
        for crop in crop_list:
            if crop.embedding is not None and crop.embedding_model == self.embedding_model:
                # Use existing embedding
                embeddings.append(np.array(crop.embedding))
            else:
                # Generate new embedding
                try:
                    crop_path = crop.crop_image_path.path
                    embedding_obj = embedding_service.generate_embedding(crop_path)
                    embeddings.append(embedding_obj.vector)
                    
                    # Save embedding to database
                    crop.embedding = embedding_obj.vector.tolist()
                    crop.embedding_model = self.embedding_model
                    crop.save(update_fields=['embedding', 'embedding_model', 'updated_at'])
                except Exception:
                    embeddings.append(None)
        
        # Filter out None embeddings
        valid_indices = [i for i, e in enumerate(embeddings) if e is not None]
        valid_embeddings = [embeddings[i] for i in valid_indices]
        valid_crops = [crop_list[i] for i in valid_indices]
        
        if not valid_embeddings:
            return {
                'status': 'no_valid_embeddings',
                'message': 'Could not generate embeddings for any crops',
                'clusters_found': 0,
                'students_created': 0,
                'crops_assigned': 0
            }
        
        # Perform clustering
        clustering_service = ClusteringService(
            max_clusters=self.max_clusters,
            similarity_threshold=self.similarity_threshold
        )
        
        cluster_result = clustering_service.cluster_embeddings(valid_embeddings)
        
        students_created = 0
        crops_assigned = 0
        cluster_student_map = {}
        
        if create_students:
            # Create a student for each cluster
            for cluster_id in range(cluster_result.num_clusters):
                cluster_indices = cluster_result.get_cluster_members(cluster_id)
                
                # Create student name
                student_name = f"Class_{session.class_session.name}_Session_{session.name}_Cluster_{cluster_id + 1}"
                
                # Split into first and last name
                # Use "Unknown" as first name and the full pattern as last name
                student = Student.objects.create(
                    class_enrolled=session.class_session,
                    first_name="Unknown",
                    last_name=student_name,
                    student_id=f"cluster_{session.id}_{cluster_id}"
                )
                
                cluster_student_map[cluster_id] = student
                students_created += 1
                
                if assign_crops:
                    # Assign crops to this student
                    for idx in cluster_indices:
                        crop = valid_crops[idx]
                        if not crop.is_identified:
                            crop.identify_student(student, confidence=None)
                            crops_assigned += 1
        
        return {
            'status': 'success',
            'session_id': session_id,
            'session_name': session.name,
            'class_id': session.class_session.id,
            'class_name': session.class_session.name,
            'total_crops': len(crop_list),
            'valid_crops': len(valid_crops),
            'clusters_found': cluster_result.num_clusters,
            'students_created': students_created,
            'crops_assigned': crops_assigned,
            'cluster_sizes': cluster_result.cluster_sizes,
            'embedding_model': self.embedding_model,
            'parameters': {
                'max_clusters': self.max_clusters,
                'similarity_threshold': self.similarity_threshold
            }
        }
    
    def cluster_class_crops(
        self,
        class_id: int,
        create_students: bool = True,
        assign_crops: bool = True,
        include_identified: bool = False
    ) -> Dict[str, Any]:
        """
        Cluster all face crops across all sessions in a class.
        
        Args:
            class_id: ID of the class to cluster
            create_students: Whether to create Student records for clusters
            assign_crops: Whether to assign face crops to created students
            include_identified: Whether to include already identified crops
        
        Returns:
            Dictionary with clustering results and statistics
        """
        from attendance.models import Class, FaceCrop, Student
        from attendance.services import EmbeddingService
        
        # Get class
        try:
            class_obj = Class.objects.get(id=class_id)
        except Class.DoesNotExist:
            raise ValueError(f"Class with ID {class_id} not found")
        
        # Get all face crops in the class
        face_crops = FaceCrop.objects.filter(
            image__session__class_session=class_obj
        ).select_related('image', 'student', 'image__session')
        
        if not include_identified:
            face_crops = face_crops.filter(is_identified=False)
        
        if not face_crops.exists():
            return {
                'status': 'no_crops',
                'message': 'No face crops found in class',
                'clusters_found': 0,
                'students_created': 0,
                'crops_assigned': 0
            }
        
        # Generate embeddings if not available
        embedding_service = EmbeddingService(model_name=self.embedding_model)
        embeddings = []
        crop_list = list(face_crops)
        
        for crop in crop_list:
            if crop.embedding is not None and crop.embedding_model == self.embedding_model:
                embeddings.append(np.array(crop.embedding))
            else:
                try:
                    crop_path = crop.crop_image_path.path
                    embedding_obj = embedding_service.generate_embedding(crop_path)
                    embeddings.append(embedding_obj.vector)
                    
                    # Save embedding
                    crop.embedding = embedding_obj.vector.tolist()
                    crop.embedding_model = self.embedding_model
                    crop.save(update_fields=['embedding', 'embedding_model', 'updated_at'])
                except Exception:
                    embeddings.append(None)
        
        # Filter valid embeddings
        valid_indices = [i for i, e in enumerate(embeddings) if e is not None]
        valid_embeddings = [embeddings[i] for i in valid_indices]
        valid_crops = [crop_list[i] for i in valid_indices]
        
        if not valid_embeddings:
            return {
                'status': 'no_valid_embeddings',
                'message': 'Could not generate embeddings for any crops',
                'clusters_found': 0,
                'students_created': 0,
                'crops_assigned': 0
            }
        
        # Perform clustering
        clustering_service = ClusteringService(
            max_clusters=self.max_clusters,
            similarity_threshold=self.similarity_threshold
        )
        
        cluster_result = clustering_service.cluster_embeddings(valid_embeddings)
        
        students_created = 0
        crops_assigned = 0
        cluster_student_map = {}
        
        if create_students:
            # Create a student for each cluster
            for cluster_id in range(cluster_result.num_clusters):
                cluster_indices = cluster_result.get_cluster_members(cluster_id)
                
                # Create student name
                student_name = f"Class_{class_obj.name}_Cluster_{cluster_id + 1}"
                
                # Check if student already exists
                existing_student = Student.objects.filter(
                    class_enrolled=class_obj,
                    first_name="Unknown",
                    last_name=student_name
                ).first()
                
                if existing_student:
                    student = existing_student
                else:
                    student = Student.objects.create(
                        class_enrolled=class_obj,
                        first_name="Unknown",
                        last_name=student_name,
                        student_id=f"cluster_{class_id}_{cluster_id}"
                    )
                    students_created += 1
                
                cluster_student_map[cluster_id] = student
                
                if assign_crops:
                    # Assign crops to this student
                    for idx in cluster_indices:
                        crop = valid_crops[idx]
                        if not crop.is_identified or include_identified:
                            crop.identify_student(student, confidence=None)
                            crops_assigned += 1
        
        return {
            'status': 'success',
            'class_id': class_id,
            'class_name': class_obj.name,
            'total_crops': len(crop_list),
            'valid_crops': len(valid_crops),
            'clusters_found': cluster_result.num_clusters,
            'students_created': students_created,
            'crops_assigned': crops_assigned,
            'cluster_sizes': cluster_result.cluster_sizes,
            'embedding_model': self.embedding_model,
            'parameters': {
                'max_clusters': self.max_clusters,
                'similarity_threshold': self.similarity_threshold,
                'include_identified': include_identified
            }
        }
