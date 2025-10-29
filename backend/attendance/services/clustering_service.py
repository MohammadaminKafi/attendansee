"""
Clustering Service for Face Crop Grouping

This service provides functionality to cluster face crops within a session
based on their embedding similarity, automatically creating and assigning
students to clusters.

Key Features:
- Agglomerative clustering using cosine distance
- Respects existing student assignments (constraint-based clustering)
- Auto-creates students for new clusters: Session_{name}_Student_{i}
- Supports force clustering mode vs allowing outliers
"""

import numpy as np
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from django.db import transaction
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity

from attendance.models import Session, Student, FaceCrop


class ClusteringService:
    """
    Service for clustering face crops and managing student assignments.
    """
    
    @staticmethod
    def cluster_session_crops(
        session_id: int,
        max_clusters: int = 10,
        force_clustering: bool = False,
        similarity_threshold: float = 0.7
    ) -> Dict:
        """
        Cluster face crops in a session based on embedding similarity.
        
        Algorithm:
        1. Separate crops with existing student assignments
        2. Create fixed clusters for each existing student
        3. Cluster unidentified crops using Agglomerative Clustering
        4. Create new students for new clusters
        5. Assign crops to appropriate students
        6. Optionally handle outliers (force_clustering mode)
        
        Args:
            session_id: ID of the session to cluster
            max_clusters: Maximum number of clusters to create
            force_clustering: If True, force all crops into clusters
            similarity_threshold: Minimum similarity for cluster membership (0-1)
        
        Returns:
            Dict containing:
            - status: 'success' or 'error'
            - clusters: List of cluster information
            - unclustered_crops: List of crop IDs not assigned to clusters
            - stats: Statistics about the clustering operation
        
        Raises:
            ValueError: If session doesn't exist or has insufficient crops
        """
        # Get session
        try:
            session = Session.objects.select_related('class_session').get(id=session_id)
        except Session.DoesNotExist:
            raise ValueError(f"Session with id {session_id} does not exist")
        
        # Get all face crops with embeddings from this session
        # Ignore crops without embeddings
        crops_query = FaceCrop.objects.filter(
            image__session=session,
            embedding__isnull=False
        ).select_related('student', 'image')
        
        crops = list(crops_query)
        
        # Validate sufficient crops
        if len(crops) < 2:
            raise ValueError(
                f"Insufficient crops with embeddings. Found {len(crops)}, need at least 2 for clustering."
            )
        
        # Separate identified and unidentified crops
        identified_crops, unidentified_crops = ClusteringService._separate_crops(crops)
        
        # Create fixed clusters for existing students
        student_clusters = ClusteringService._create_student_clusters(identified_crops)
        
        # If no unidentified crops, just return existing clusters
        if not unidentified_crops:
            return ClusteringService._format_results(
                session=session,
                student_clusters=student_clusters,
                new_clusters=[],
                unclustered_crop_ids=[],
                students_created=0
            )
        
        # Calculate remaining cluster budget
        existing_cluster_count = len(student_clusters)
        available_clusters = max(1, max_clusters - existing_cluster_count)
        
        # Cluster unidentified crops
        new_clusters, unclustered_crops_list = ClusteringService._cluster_unidentified_crops(
            unidentified_crops=unidentified_crops,
            n_clusters=min(available_clusters, len(unidentified_crops)),
            similarity_threshold=similarity_threshold,
            force_clustering=force_clustering
        )
        
        # Assign students to new clusters (within transaction)
        with transaction.atomic():
            students_created = ClusteringService._assign_students_to_clusters(
                session=session,
                new_clusters=new_clusters,
                student_clusters=student_clusters
            )
            
            # Handle force clustering for outliers
            if force_clustering and unclustered_crops_list:
                ClusteringService._force_assign_outliers(
                    unclustered_crops_list,
                    student_clusters,
                    new_clusters
                )
                unclustered_crops_list = []  # All assigned
        
        # Format and return results
        return ClusteringService._format_results(
            session=session,
            student_clusters=student_clusters,
            new_clusters=new_clusters,
            unclustered_crop_ids=[c.id for c in unclustered_crops_list],
            students_created=students_created
        )
    
    @staticmethod
    def _separate_crops(crops: List[FaceCrop]) -> Tuple[List[FaceCrop], List[FaceCrop]]:
        """Separate crops into identified and unidentified."""
        identified = [c for c in crops if c.is_identified and c.student_id]
        unidentified = [c for c in crops if not c.is_identified or not c.student_id]
        return identified, unidentified
    
    @staticmethod
    def _create_student_clusters(identified_crops: List[FaceCrop]) -> Dict[int, Dict]:
        """
        Create fixed clusters for crops with existing student assignments.
        
        Returns:
            Dict mapping student_id to cluster info with crops list
        """
        student_clusters = defaultdict(lambda: {'crops': [], 'student': None})
        
        for crop in identified_crops:
            student_id = crop.student_id
            if student_clusters[student_id]['student'] is None:
                student_clusters[student_id]['student'] = crop.student
            student_clusters[student_id]['crops'].append(crop)
        
        return dict(student_clusters)
    
    @staticmethod
    def _cluster_unidentified_crops(
        unidentified_crops: List[FaceCrop],
        n_clusters: int,
        similarity_threshold: float,
        force_clustering: bool
    ) -> Tuple[List[Dict], List[FaceCrop]]:
        """
        Cluster unidentified crops using Agglomerative Clustering.
        
        Returns:
            Tuple of (new_clusters, unclustered_crops)
        """
        if not unidentified_crops:
            return [], []
        
        # Ensure n_clusters is valid
        n_clusters = min(n_clusters, len(unidentified_crops))
        n_clusters = max(1, n_clusters)
        
        # Extract embeddings
        embeddings = np.array([crop.embedding for crop in unidentified_crops])
        
        # Calculate cosine similarity and convert to distance
        similarity_matrix = cosine_similarity(embeddings)
        distance_matrix = 1 - similarity_matrix
        
        # Run Agglomerative Clustering
        clustering = AgglomerativeClustering(
            n_clusters=n_clusters,
            metric='precomputed',
            linkage='average'
        )
        
        try:
            labels = clustering.fit_predict(distance_matrix)
        except Exception as e:
            # Fallback: single cluster
            labels = np.zeros(len(unidentified_crops), dtype=int)
        
        # Group crops by cluster label
        clusters_dict = defaultdict(list)
        for crop, label in zip(unidentified_crops, labels):
            clusters_dict[int(label)].append(crop)
        
        # Filter clusters by similarity threshold (if not force_clustering)
        new_clusters = []
        unclustered_crops = []
        
        for label, crop_list in clusters_dict.items():
            if force_clustering or len(crop_list) >= 2:
                # Calculate average intra-cluster similarity
                if len(crop_list) > 1:
                    crop_indices = [unidentified_crops.index(c) for c in crop_list]
                    cluster_similarities = similarity_matrix[np.ix_(crop_indices, crop_indices)]
                    avg_similarity = (cluster_similarities.sum() - len(crop_list)) / (len(crop_list) * (len(crop_list) - 1))
                else:
                    avg_similarity = 1.0
                
                if avg_similarity >= similarity_threshold or force_clustering:
                    new_clusters.append({
                        'label': label,
                        'crops': crop_list,
                        'avg_similarity': float(avg_similarity)
                    })
                else:
                    unclustered_crops.extend(crop_list)
            else:
                # Single-crop clusters are outliers (unless force_clustering)
                if force_clustering:
                    new_clusters.append({
                        'label': label,
                        'crops': crop_list,
                        'avg_similarity': 1.0
                    })
                else:
                    unclustered_crops.extend(crop_list)
        
        return new_clusters, unclustered_crops
    
    @staticmethod
    def _assign_students_to_clusters(
        session: Session,
        new_clusters: List[Dict],
        student_clusters: Dict[int, Dict]
    ) -> int:
        """
        Create students and assign crops to clusters.
        
        Returns:
            Number of students created
        """
        students_created = 0
        next_student_num = len(student_clusters) + 1
        
        for cluster in new_clusters:
            # Create student for this cluster
            student = Student.objects.create(
                class_enrolled=session.class_session,
                first_name=f'Session_{session.name}',
                last_name=f'Student_{next_student_num}',
                student_id=f'AUTO_S{session.id}_C{next_student_num}'
            )
            students_created += 1
            
            # Assign all crops to this student
            for crop in cluster['crops']:
                crop.identify_student(
                    student=student,
                    confidence=cluster.get('avg_similarity', 0.8)
                )
            
            # Add to student_clusters for reference
            cluster['student'] = student
            next_student_num += 1
        
        return students_created
    
    @staticmethod
    def _force_assign_outliers(
        unclustered_crops: List[FaceCrop],
        student_clusters: Dict[int, Dict],
        new_clusters: List[Dict]
    ):
        """
        Force assign outlier crops to nearest cluster.
        """
        if not unclustered_crops:
            return
        
        # Collect all cluster centroids
        all_clusters = []
        
        # Add existing student clusters
        for student_id, cluster_info in student_clusters.items():
            crops = cluster_info['crops']
            if crops:
                embeddings = np.array([c.embedding for c in crops])
                centroid = embeddings.mean(axis=0)
                all_clusters.append({
                    'student': cluster_info['student'],
                    'centroid': centroid
                })
        
        # Add new clusters
        for cluster in new_clusters:
            crops = cluster['crops']
            if crops:
                embeddings = np.array([c.embedding for c in crops])
                centroid = embeddings.mean(axis=0)
                all_clusters.append({
                    'student': cluster['student'],
                    'centroid': centroid
                })
        
        if not all_clusters:
            return
        
        # Assign each outlier to nearest cluster
        for crop in unclustered_crops:
            crop_embedding = np.array(crop.embedding)
            
            # Find nearest cluster
            max_similarity = -1
            nearest_student = None
            
            for cluster in all_clusters:
                similarity = float(cosine_similarity([crop_embedding], [cluster['centroid']])[0][0])
                if similarity > max_similarity:
                    max_similarity = similarity
                    nearest_student = cluster['student']
            
            if nearest_student:
                crop.identify_student(
                    student=nearest_student,
                    confidence=max(0.3, max_similarity * 0.6)  # Lower confidence for forced assignment
                )
    
    @staticmethod
    def _format_results(
        session: Session,
        student_clusters: Dict[int, Dict],
        new_clusters: List[Dict],
        unclustered_crop_ids: List[int],
        students_created: int
    ) -> Dict:
        """Format clustering results for API response."""
        clusters_output = []
        
        # Add existing student clusters
        for student_id, cluster_info in student_clusters.items():
            student = cluster_info['student']
            crops = cluster_info['crops']
            clusters_output.append({
                'cluster_id': student_id,
                'student_id': student.id,
                'student_name': student.full_name,
                'crop_ids': [c.id for c in crops],
                'crop_count': len(crops),
                'is_existing_student': True
            })
        
        # Add new clusters
        for i, cluster in enumerate(new_clusters):
            student = cluster['student']
            crops = cluster['crops']
            clusters_output.append({
                'cluster_id': 1000 + i,  # Offset to distinguish from student IDs
                'student_id': student.id,
                'student_name': student.full_name,
                'crop_ids': [c.id for c in crops],
                'crop_count': len(crops),
                'is_existing_student': False
            })
        
        # Calculate statistics
        total_crops = sum(c['crop_count'] for c in clusters_output) + len(unclustered_crop_ids)
        clustered_crops = sum(c['crop_count'] for c in clusters_output)
        
        return {
            'status': 'success',
            'session_id': session.id,
            'session_name': session.name,
            'clusters': clusters_output,
            'unclustered_crops': unclustered_crop_ids,
            'stats': {
                'total_crops': total_crops,
                'clustered_crops': clustered_crops,
                'unclustered_crops': len(unclustered_crop_ids),
                'clusters_created': len(clusters_output),
                'students_created': students_created,
                'existing_students_used': len(student_clusters)
            }
        }
    
    @staticmethod
    def cluster_class_crops(
        class_id: int,
        max_clusters: int = 10,
        force_clustering: bool = False,
        similarity_threshold: float = 0.7
    ) -> Dict:
        """
        Cluster face crops across all sessions in a class based on embedding similarity.
        
        This method processes all face crops from all sessions in a class and creates
        students at the class level, useful for identifying the same person across
        multiple sessions.
        
        Algorithm:
        1. Get all face crops with embeddings from all sessions in the class
        2. Separate crops with existing student assignments
        3. Create fixed clusters for each existing student
        4. Cluster unidentified crops using Agglomerative Clustering
        5. Create new students at class level for new clusters
        6. Assign crops to appropriate students
        7. Optionally handle outliers (force_clustering mode)
        
        Args:
            class_id: ID of the class to cluster
            max_clusters: Maximum number of clusters to create
            force_clustering: If True, force all crops into clusters
            similarity_threshold: Minimum similarity for cluster membership (0-1)
        
        Returns:
            Dict containing:
            - status: 'success' or 'error'
            - total_face_crops: Total number of crops processed
            - crops_with_embeddings: Crops that have embeddings
            - crops_without_embeddings: Crops without embeddings (ignored)
            - identified_crops: Crops already assigned to students
            - unidentified_crops: Crops not assigned before clustering
            - clusters_created: Number of clusters created
            - students_created: Number of new students created
            - crops_assigned: Number of crops assigned to clusters
            - outliers: Number of crops remaining unassigned
            - student_names: List of created student names
            - session_breakdown: Per-session statistics
            - error: Error message if any
        
        Raises:
            ValueError: If class doesn't exist or has insufficient crops
        """
        from attendance.models import Class
        
        # Get class
        try:
            class_obj = Class.objects.get(id=class_id)
        except Class.DoesNotExist:
            raise ValueError(f"Class with id {class_id} does not exist")
        
        # Get all sessions in the class
        sessions = list(class_obj.sessions.all())
        if not sessions:
            raise ValueError(f"Class '{class_obj.name}' has no sessions")
        
        # Get all face crops with embeddings from all sessions in the class
        # Ignore crops without embeddings
        crops_query = FaceCrop.objects.filter(
            image__session__class_session=class_obj,
            embedding__isnull=False
        ).select_related('student', 'image', 'image__session')
        
        crops = list(crops_query)
        
        # Get counts for statistics
        all_crops = FaceCrop.objects.filter(image__session__class_session=class_obj)
        total_face_crops = all_crops.count()
        crops_without_embeddings = all_crops.filter(embedding__isnull=True).count()
        
        # Validate sufficient crops
        if len(crops) < 2:
            raise ValueError(
                f"Insufficient crops with embeddings. Found {len(crops)}, need at least 2 for clustering."
            )
        
        # Separate identified and unidentified crops
        identified_crops, unidentified_crops = ClusteringService._separate_crops(crops)
        
        # Create fixed clusters for existing students
        student_clusters = ClusteringService._create_student_clusters(identified_crops)
        
        # If no unidentified crops, just return existing clusters
        if not unidentified_crops:
            return ClusteringService._format_class_results(
                class_obj=class_obj,
                sessions=sessions,
                student_clusters=student_clusters,
                new_clusters=[],
                unclustered_crop_ids=[],
                students_created=0,
                total_face_crops=total_face_crops,
                crops_with_embeddings=len(crops),
                crops_without_embeddings=crops_without_embeddings
            )
        
        # Calculate remaining cluster budget
        existing_cluster_count = len(student_clusters)
        available_clusters = max(1, max_clusters - existing_cluster_count)
        
        # Cluster unidentified crops
        new_clusters, unclustered_crops_list = ClusteringService._cluster_unidentified_crops(
            unidentified_crops=unidentified_crops,
            n_clusters=min(available_clusters, len(unidentified_crops)),
            similarity_threshold=similarity_threshold,
            force_clustering=force_clustering
        )
        
        # Assign students to new clusters (within transaction)
        with transaction.atomic():
            students_created = ClusteringService._assign_students_to_class_clusters(
                class_obj=class_obj,
                new_clusters=new_clusters,
                student_clusters=student_clusters
            )
            
            # Handle force clustering for outliers
            if force_clustering and unclustered_crops_list:
                ClusteringService._force_assign_outliers(
                    unclustered_crops_list,
                    student_clusters,
                    new_clusters
                )
                unclustered_crops_list = []  # All assigned
        
        # Format and return results
        return ClusteringService._format_class_results(
            class_obj=class_obj,
            sessions=sessions,
            student_clusters=student_clusters,
            new_clusters=new_clusters,
            unclustered_crop_ids=[c.id for c in unclustered_crops_list],
            students_created=students_created,
            total_face_crops=total_face_crops,
            crops_with_embeddings=len(crops),
            crops_without_embeddings=crops_without_embeddings
        )
    
    @staticmethod
    def _assign_students_to_class_clusters(
        class_obj,
        new_clusters: List[Dict],
        student_clusters: Dict[int, Dict]
    ) -> int:
        """
        Create students at class level and assign crops to clusters.
        
        Returns:
            Number of students created
        """
        students_created = 0
        next_student_num = len(student_clusters) + 1
        
        for cluster in new_clusters:
            # Create student for this cluster at class level
            student = Student.objects.create(
                class_enrolled=class_obj,
                first_name=f'Class_{class_obj.name}',
                last_name=f'Student_{next_student_num}',
                student_id=f'AUTO_C{class_obj.id}_S{next_student_num}'
            )
            students_created += 1
            
            # Assign all crops to this student
            for crop in cluster['crops']:
                crop.identify_student(
                    student=student,
                    confidence=cluster.get('avg_similarity', 0.8)
                )
            
            # Add to student_clusters for reference
            cluster['student'] = student
            next_student_num += 1
        
        return students_created
    
    @staticmethod
    def _format_class_results(
        class_obj,
        sessions: List[Session],
        student_clusters: Dict[int, Dict],
        new_clusters: List[Dict],
        unclustered_crop_ids: List[int],
        students_created: int,
        total_face_crops: int,
        crops_with_embeddings: int,
        crops_without_embeddings: int
    ) -> Dict:
        """Format class-level clustering results for API response."""
        
        # Collect all crops that were assigned
        all_assigned_crops = []
        for cluster_info in student_clusters.values():
            all_assigned_crops.extend(cluster_info['crops'])
        for cluster in new_clusters:
            all_assigned_crops.extend(cluster['crops'])
        
        # Create per-session breakdown
        session_breakdown = []
        for session in sessions:
            session_crops = [c for c in all_assigned_crops if c.image.session_id == session.id]
            session_breakdown.append({
                'session_id': session.id,
                'session_name': session.name,
                'crops_assigned': len(session_crops),
                'unique_students': len(set(c.student_id for c in session_crops if c.student_id))
            })
        
        # Get list of created student names
        student_names = []
        for cluster in new_clusters:
            if 'student' in cluster:
                student_names.append(cluster['student'].full_name)
        
        # Calculate statistics
        total_assigned = len(all_assigned_crops)
        
        return {
            'status': 'success',
            'class_id': class_obj.id,
            'class_name': class_obj.name,
            'total_face_crops': total_face_crops,
            'crops_with_embeddings': crops_with_embeddings,
            'crops_without_embeddings': crops_without_embeddings,
            'identified_crops': len([c for c in all_assigned_crops if c.id not in [cl['crops'] for cl in new_clusters for _ in cl['crops']]]),
            'unidentified_crops': sum(len(c['crops']) for c in new_clusters),
            'clusters_created': len(student_clusters) + len(new_clusters),
            'students_created': students_created,
            'crops_assigned': total_assigned,
            'outliers': len(unclustered_crop_ids),
            'student_names': student_names,
            'session_breakdown': session_breakdown
        }
