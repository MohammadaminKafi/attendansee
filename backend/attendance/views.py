from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Count, Q
from django.utils import timezone
from django.http import HttpResponse
import os
from .models import Class, Student, Session, Image, FaceCrop
from .serializers import (
    ClassSerializer, StudentSerializer, SessionSerializer,
    ImageSerializer, FaceCropSerializer, FaceCropDetailSerializer,
    BulkStudentUploadSerializer, ProcessImageSerializer,
    AggregateCropsSerializer, AggregateClassSerializer, MergeStudentSerializer,
    GenerateEmbeddingSerializer, ClusterCropsSerializer
)
from .permissions import IsOwnerOrAdmin, IsClassOwnerOrAdmin


class ClassViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Class model.
    
    Admins: Full CRUD access to all classes
    Users: Can create, read, update, delete their own classes
    """
    serializer_class = ClassSerializer
    permission_classes = [IsAuthenticated, IsClassOwnerOrAdmin]
    
    def get_queryset(self):
        """
        Return all classes for admin users.
        Return only owned classes for regular users.
        """
        user = self.request.user
        if user.is_staff:
            return Class.objects.all().order_by('-created_at')
        return Class.objects.filter(owner=user).order_by('-created_at')
    
    def perform_create(self, serializer):
        """
        Set the owner to the current user when creating a class.
        """
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        """
        Get all students in a class.
        """
        class_obj = self.get_object()
        students = class_obj.students.all()
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def sessions(self, request, pk=None):
        """
        Get all sessions in a class.
        """
        class_obj = self.get_object()
        sessions = class_obj.sessions.all().order_by('-date')
        serializer = SessionSerializer(sessions, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """
        Get statistics for a class.
        """
        class_obj = self.get_object()
        
        # Get total and processed images
        total_images = Image.objects.filter(session__class_session=class_obj).count()
        processed_images = Image.objects.filter(
            session__class_session=class_obj,
            is_processed=True
        ).count()
        
        # Get face crop counts
        all_face_crops = FaceCrop.objects.filter(
            image__session__class_session=class_obj
        )
        total_face_crops = all_face_crops.count()
        crops_with_embeddings = all_face_crops.filter(embedding__isnull=False).count()
        crops_without_embeddings = all_face_crops.filter(embedding__isnull=True).count()
        
        stats = {
            'student_count': class_obj.students.count(),
            'session_count': class_obj.sessions.count(),
            'total_images': total_images,
            'processed_images': processed_images,
            'unprocessed_images_count': total_images - processed_images,
            'total_face_crops': total_face_crops,
            'crops_with_embeddings': crops_with_embeddings,
            'crops_without_embeddings': crops_without_embeddings,
            'identified_faces': all_face_crops.filter(is_identified=True).count(),
        }
        
        return Response(stats)
    
    @action(
        detail=True,
        methods=['post'],
        parser_classes=[MultiPartParser, FormParser],
        url_path='bulk-upload-students'
    )
    def bulk_upload_students(self, request, pk=None):
        """
        Bulk upload students from CSV or Excel file.
        
        Expected file format:
        - CSV or Excel file (.csv, .xlsx, .xls)
        - Columns: first_name, last_name, student_id (optional)
        - File can have header row or not (specify with has_header parameter)
        
        Parameters:
        - file: The CSV/Excel file
        - has_header: Boolean indicating if file has header row (default: true)
        
        Returns:
        - created: List of created students
        - total_created: Number of students created
        - total_skipped: Number of students skipped (duplicates)
        - skipped: List of skipped students with reasons
        """
        class_obj = self.get_object()
        
        serializer = BulkStudentUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        file = serializer.validated_data['file']
        has_header = serializer.validated_data.get('has_header', True)
        
        # Determine file type and parse accordingly
        file_extension = file.name.split('.')[-1].lower()
        
        try:
            if file_extension == 'csv':
                students_data = serializer.parse_csv_file(file, has_header)
            elif file_extension in ['xlsx', 'xls']:
                students_data = serializer.parse_excel_file(file, has_header)
            else:
                return Response(
                    {'error': 'Unsupported file format'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create students
        result = serializer.create_students(class_obj, students_data)
        
        # Serialize created students
        created_students_data = StudentSerializer(
            result['created'],
            many=True
        ).data
        
        return Response({
            'created': created_students_data,
            'total_created': result['total_created'],
            'total_skipped': result['total_skipped'],
            'skipped': result['skipped'],
            'message': f"Successfully created {result['total_created']} students. "
                      f"Skipped {result['total_skipped']} duplicates."
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], url_path='aggregate-class')
    def aggregate_class(self, request, pk=None):
        """
        Aggregate attendance data across all sessions in the class.
        
        This endpoint provides unified statistics and attendance patterns
        across all sessions in the class. The actual aggregation logic
        will be implemented later using the core face recognition module.
        
        Parameters (optional):
        - include_unprocessed: Include unprocessed sessions (default: false)
        - date_from: Start date for aggregation (YYYY-MM-DD)
        - date_to: End date for aggregation (YYYY-MM-DD)
        
        Returns:
        - Aggregated attendance statistics
        - Per-student attendance summary
        - Session-wise breakdown
        """
        class_obj = self.get_object()
        
        serializer = AggregateClassSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        include_unprocessed = serializer.validated_data.get('include_unprocessed', False)
        date_from = serializer.validated_data.get('date_from')
        date_to = serializer.validated_data.get('date_to')
        
        # Filter sessions based on parameters
        sessions_query = Session.objects.filter(class_session=class_obj)
        
        if not include_unprocessed:
            sessions_query = sessions_query.filter(is_processed=True)
        
        if date_from:
            sessions_query = sessions_query.filter(date__gte=date_from)
        
        if date_to:
            sessions_query = sessions_query.filter(date__lte=date_to)
        
        sessions = sessions_query.order_by('date')
        
        # TODO: Implement actual aggregation logic here
        # This is a stub implementation that will be completed later
        # The actual implementation will:
        # 1. Load face embeddings from all sessions
        # 2. Perform cross-session face matching
        # 3. Generate unified attendance records
        # 4. Calculate attendance patterns and statistics
        
        # For now, return basic statistics
        all_students = class_obj.students.all()
        student_stats = []
        
        for student in all_students:
            attended_sessions = sessions.filter(
                images__face_crops__student=student
            ).distinct().count()
            
            student_stats.append({
                'student_id': student.id,
                'name': student.full_name,
                'student_number': student.student_id,
                'total_sessions': sessions.count(),
                'attended_sessions': attended_sessions,
                'attendance_rate': round(
                    (attended_sessions / sessions.count() * 100) if sessions.count() > 0 else 0,
                    2
                ),
                'total_detections': student.face_crops.filter(
                    image__session__in=sessions
                ).count()
            })
        
        return Response({
            'class_id': class_obj.id,
            'class_name': class_obj.name,
            'total_sessions': sessions.count(),
            'total_students': all_students.count(),
            'date_range': {
                'from': sessions.first().date if sessions.exists() else None,
                'to': sessions.last().date if sessions.exists() else None
            },
            'student_statistics': student_stats,
            'message': 'Class aggregation completed successfully. '
                      'Note: Full aggregation logic will be implemented with core face recognition module.'
        })
    
    @action(detail=True, methods=['get'], url_path='attendance-report')
    def attendance_report(self, request, pk=None):
        """
        Get attendance report matrix for the class.
        
        Returns a matrix showing which students attended which sessions.
        This is useful for displaying in a tabular format.
        
        Query Parameters:
        - include_unprocessed: Include unprocessed sessions (default: false)
        - date_from: Start date filter (YYYY-MM-DD)
        - date_to: End date filter (YYYY-MM-DD)
        
        Returns:
        - List of students with attendance data
        - List of sessions
        - Attendance matrix (student_id -> session_id -> present/absent)
        """
        class_obj = self.get_object()
        
        # Get query parameters
        include_unprocessed = request.query_params.get('include_unprocessed', 'false').lower() == 'true'
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        # Filter sessions
        sessions_query = Session.objects.filter(class_session=class_obj)
        
        if not include_unprocessed:
            sessions_query = sessions_query.filter(is_processed=True)
        
        if date_from:
            try:
                from datetime import datetime
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                sessions_query = sessions_query.filter(date__gte=date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                from datetime import datetime
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                sessions_query = sessions_query.filter(date__lte=date_to_obj)
            except ValueError:
                pass
        
        sessions = sessions_query.order_by('date', 'created_at')
        
        # Get all students
        students = class_obj.students.all().order_by('last_name', 'first_name')
        
        # Build attendance matrix
        attendance_matrix = []
        
        for student in students:
            # Get sessions this student attended
            attended_session_ids = set(
                Session.objects.filter(
                    id__in=sessions.values_list('id', flat=True),
                    images__face_crops__student=student
                ).distinct().values_list('id', flat=True)
            )
            
            # Build attendance record for each session
            session_attendance = []
            for session in sessions:
                detection_count = FaceCrop.objects.filter(
                    image__session=session,
                    student=student
                ).count()
                
                session_attendance.append({
                    'session_id': session.id,
                    'present': session.id in attended_session_ids,
                    'detection_count': detection_count
                })
            
            # Calculate student statistics
            attended_count = len(attended_session_ids)
            total_sessions = sessions.count()
            attendance_rate = (attended_count / total_sessions * 100) if total_sessions > 0 else 0
            
            attendance_matrix.append({
                'student_id': student.id,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'full_name': student.full_name,
                'student_number': student.student_id,
                'email': student.email,
                'attended_sessions': attended_count,
                'total_sessions': total_sessions,
                'attendance_rate': round(attendance_rate, 2),
                'session_attendance': session_attendance
            })
        
        # Build session summary
        session_summary = []
        for session in sessions:
            present_count = Student.objects.filter(
                class_enrolled=class_obj,
                face_crops__image__session=session
            ).distinct().count()
            
            session_summary.append({
                'id': session.id,
                'name': session.name,
                'date': session.date,
                'start_time': session.start_time,
                'end_time': session.end_time,
                'is_processed': session.is_processed,
                'present_count': present_count,
                'total_students': students.count(),
                'attendance_rate': round((present_count / students.count() * 100) if students.count() > 0 else 0, 2)
            })
        
        return Response({
            'class_id': class_obj.id,
            'class_name': class_obj.name,
            'total_students': students.count(),
            'total_sessions': sessions.count(),
            'date_range': {
                'from': sessions.first().date if sessions.exists() else None,
                'to': sessions.last().date if sessions.exists() else None
            },
            'sessions': session_summary,
            'attendance_matrix': attendance_matrix
        })
    
    @action(detail=True, methods=['get'], url_path='export-attendance-pdf')
    def export_attendance_pdf(self, request, pk=None):
        """
        Export attendance report as PDF with face crop images.
        
        Generates a PDF report showing each student's attendance with one face crop
        image from each attended session along with session information.
        
        Returns:
        - PDF file download
        """
        from .services import AttendancePDFService
        
        class_obj = self.get_object()
        
        # Generate the PDF using the service
        try:
            pdf_service = AttendancePDFService(class_obj)
            pdf_buffer = pdf_service.generate_report()
            
            # Create the HTTP response with PDF
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            filename = f"{class_obj.name.replace(' ', '_')}_attendance_report.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
        except Exception as e:
            return Response(
                {'error': f'Failed to generate PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='process-all-images')
    def process_all_images(self, request, pk=None):
        """
        Process all unprocessed images in the class.
        
        This endpoint processes all unprocessed images across all sessions
        in the class using the specified face detection parameters.
        
        Parameters:
        - detector_backend: Detector to use (default: 'retinaface')
        - confidence_threshold: Detection confidence threshold (default: 0.5)
        - apply_background_effect: Apply background effect (default: true)
        - rectangle_color: RGB color for rectangles (default: [0, 255, 0])
        - rectangle_thickness: Rectangle thickness (default: 2)
        
        Returns:
        - Total images found
        - Images processed
        - Images failed
        - Total faces detected
        """
        from attendance.utils import process_image_with_face_detection
        from attendance.serializers import BulkProcessImagesSerializer
        
        class_obj = self.get_object()
        
        # Validate request data
        serializer = BulkProcessImagesSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Get processing parameters
        detector_backend = serializer.validated_data.get('detector_backend', 'retinaface')
        confidence_threshold = serializer.validated_data.get('confidence_threshold', 0.5)
        apply_background_effect = serializer.validated_data.get('apply_background_effect', True)
        rectangle_color = tuple(serializer.validated_data.get('rectangle_color', [0, 255, 0]))
        rectangle_thickness = serializer.validated_data.get('rectangle_thickness', 2)
        
        # Get all unprocessed images in the class
        unprocessed_images = Image.objects.filter(
            session__class_session=class_obj,
            is_processed=False
        )
        
        if not unprocessed_images.exists():
            return Response({
                'status': 'completed',
                'message': 'No unprocessed images found in this class',
                'total_images': 0,
                'processed_count': 0,
                'failed_count': 0,
                'total_faces_detected': 0
            })
        
        # Process each image
        processed_count = 0
        failed_count = 0
        total_faces = 0
        errors = []
        
        for image in unprocessed_images:
            try:
                result = process_image_with_face_detection(
                    image_obj=image,
                    detector_backend=detector_backend,
                    min_confidence=confidence_threshold,
                    apply_background_effect=apply_background_effect,
                    rectangle_color=rectangle_color,
                    rectangle_thickness=rectangle_thickness
                )
                processed_count += 1
                total_faces += result['faces_detected']
            except Exception as e:
                failed_count += 1
                errors.append({
                    'image_id': image.id,
                    'session_id': image.session.id,
                    'error': str(e)
                })
        
        return Response({
            'status': 'completed',
            'class_id': class_obj.id,
            'class_name': class_obj.name,
            'total_images': unprocessed_images.count(),
            'processed_count': processed_count,
            'failed_count': failed_count,
            'total_faces_detected': total_faces,
            'errors': errors if errors else None
        })
    
    @action(detail=True, methods=['post'], url_path='generate-embeddings')
    def generate_embeddings(self, request, pk=None):
        """
        Generate embeddings for all face crops in the class.
        
        This endpoint generates embeddings for all face crops across all
        sessions in the class. If process_unprocessed_images is true and
        there are unprocessed images, it will process them first.
        
        Parameters:
        - model_name: Embedding model ('arcface', 'facenet512') (default: 'arcface')
        - process_unprocessed_images: Process unprocessed images first (default: false)
        - detector_backend: Detector to use if processing images (default: 'retinaface')
        - confidence_threshold: Detection confidence (default: 0.5)
        - apply_background_effect: Apply background effect (default: true)
        
        Returns:
        - Total crops found
        - Embeddings generated
        - Embeddings failed
        - Images processed (if process_unprocessed_images=true)
        """
        from attendance.services import EmbeddingService
        from attendance.utils import process_image_with_face_detection
        from attendance.serializers import BulkGenerateEmbeddingsSerializer
        
        class_obj = self.get_object()
        
        # Validate request data
        serializer = BulkGenerateEmbeddingsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Get parameters
        model_name = serializer.validated_data.get('model_name', 'arcface')
        process_unprocessed = serializer.validated_data.get('process_unprocessed_images', False)
        detector_backend = serializer.validated_data.get('detector_backend', 'retinaface')
        confidence_threshold = serializer.validated_data.get('confidence_threshold', 0.5)
        apply_background_effect = serializer.validated_data.get('apply_background_effect', True)
        
        # Check for unprocessed images
        unprocessed_images = Image.objects.filter(
            session__class_session=class_obj,
            is_processed=False
        )
        
        images_processed = 0
        
        if unprocessed_images.exists():
            if not process_unprocessed:
                return Response({
                    'error': 'Class has unprocessed images',
                    'unprocessed_count': unprocessed_images.count(),
                    'message': 'Set process_unprocessed_images=true to process them first'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Process unprocessed images first
            for image in unprocessed_images:
                try:
                    process_image_with_face_detection(
                        image_obj=image,
                        detector_backend=detector_backend,
                        min_confidence=confidence_threshold,
                        apply_background_effect=apply_background_effect,
                        rectangle_color=(0, 255, 0),
                        rectangle_thickness=2
                    )
                    images_processed += 1
                except Exception as e:
                    # Continue processing other images
                    pass
        
        # Get all face crops in the class
        all_face_crops = FaceCrop.objects.filter(
            image__session__class_session=class_obj
        )
        
        # Only process crops without embeddings
        face_crops = all_face_crops.filter(embedding__isnull=True)
        
        crops_with_embeddings = all_face_crops.filter(embedding__isnull=False).count()
        
        if not face_crops.exists():
            return Response({
                'status': 'completed',
                'message': 'All face crops already have embeddings',
                'total_crops': all_face_crops.count(),
                'crops_with_embeddings': crops_with_embeddings,
                'crops_without_embeddings': 0,
                'embeddings_generated': 0,
                'embeddings_failed': 0,
                'images_processed': images_processed
            })
        
        # Generate embeddings
        generated_count = 0
        failed_count = 0
        errors = []
        
        for crop in face_crops:
            crop_image_path = crop.crop_image_path.path if crop.crop_image_path else None
            
            if not crop_image_path or not os.path.exists(crop_image_path):
                failed_count += 1
                continue
            
            try:
                embedding = EmbeddingService.generate_embedding(
                    image_path=crop_image_path,
                    model_name=model_name
                )
                
                if embedding is not None:
                    crop.embedding = embedding
                    crop.embedding_model = model_name
                    crop.save(update_fields=['embedding', 'embedding_model', 'updated_at'])
                    generated_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                failed_count += 1
                errors.append({
                    'crop_id': crop.id,
                    'error': str(e)
                })
        
        return Response({
            'status': 'completed',
            'class_id': class_obj.id,
            'class_name': class_obj.name,
            'model_name': model_name,
            'total_crops': all_face_crops.count(),
            'crops_with_embeddings': crops_with_embeddings,
            'crops_without_embeddings': face_crops.count(),
            'embeddings_generated': generated_count,
            'embeddings_failed': failed_count,
            'images_processed': images_processed,
            'errors': errors[:10] if errors else None  # Limit to first 10 errors
        })

    @action(detail=True, methods=['post'], url_path='cluster-crops')
    def cluster_crops(self, request, pk=None):
        """
        Cluster face crops across all sessions in this class based on embedding similarity.
        Creates new Student instances for each cluster and assigns crops from all sessions.
        
        This is useful for identifying the same person across multiple sessions in a class.
        
        Constraints:
        - Face crops with existing student assignments are kept in separate clusters
        - Never mixes crops from different students in the same cluster
        - Only unidentified crops are clustered together
        - Only crops with embeddings are processed (crops without embeddings are ignored)
        
        Body params:
        - max_clusters: Maximum number of clusters (2-200)
        - force_clustering: If False, crops with low similarity stay unassigned
        - similarity_threshold: Minimum similarity for clustering (0.0-1.0)
        """
        class_obj = self.get_object()
        
        # Validate request data
        serializer = ClusterCropsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Extract validated parameters
        max_clusters = serializer.validated_data['max_clusters']
        force_clustering = serializer.validated_data['force_clustering']
        similarity_threshold = serializer.validated_data['similarity_threshold']
        
        # Import ClusteringService
        from attendance.services import ClusteringService
        
        try:
            # Run clustering
            result = ClusteringService.cluster_class_crops(
                class_id=class_obj.id,
                max_clusters=max_clusters,
                force_clustering=force_clustering,
                similarity_threshold=similarity_threshold
            )
            
            return Response({
                'status': 'success',
                'class_id': class_obj.id,
                'class_name': class_obj.name,
                **result
            })
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Clustering failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='auto-assign-all-crops')
    def auto_assign_all_crops(self, request, pk=None):
        """
        Automatically assign all unidentified face crops across all sessions in the class
        to students using similarity-based matching.
        
        This endpoint processes all unidentified crops that have embeddings across the entire
        class and attempts to assign them to students using K-Nearest Neighbors on existing
        identified crops.
        
        Body params:
        - k: Number of neighbors to consider (default: 5)
        - similarity_threshold: Minimum similarity score (0.0-1.0, default: 0.6)
        - embedding_model: Optional model filter ('arcface' or 'facenet512')
        - use_voting: Use majority voting among top-k (default: false)
        
        Returns:
        - Statistics about assignments made across all sessions
        - List of assigned crops with confidence scores
        - List of unassigned crops (with reasons)
        - Per-session breakdown
        """
        from attendance.services import AssignmentService
        
        class_obj = self.get_object()
        
        # Parse parameters with defaults
        k = int(request.data.get('k', 5))
        similarity_threshold = float(request.data.get('similarity_threshold', 0.6))
        embedding_model = request.data.get('embedding_model')
        use_voting = bool(request.data.get('use_voting', False))
        
        # Validate parameters
        if k < 1 or k > 50:
            return Response({'error': 'k must be between 1 and 50'}, status=status.HTTP_400_BAD_REQUEST)
        if similarity_threshold < 0.0 or similarity_threshold > 1.0:
            return Response({'error': 'similarity_threshold must be between 0.0 and 1.0'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get all face crops across all sessions in the class
        all_crops = FaceCrop.objects.filter(image__session__class_session=class_obj)
        
        # Filter to unidentified crops with embeddings
        unidentified_crops = all_crops.filter(
            is_identified=False,
            embedding__isnull=False
        )
        
        if embedding_model:
            unidentified_crops = unidentified_crops.filter(embedding_model=embedding_model)
        
        total_to_process = unidentified_crops.count()
        
        if total_to_process == 0:
            return Response({
                'status': 'completed',
                'message': 'No unidentified crops with embeddings found',
                'class_id': class_obj.id,
                'class_name': class_obj.name,
                'total_crops': all_crops.count(),
                'crops_to_process': 0,
                'crops_assigned': 0,
                'crops_unassigned': 0,
                'assigned_crops': [],
                'unassigned_crops': [],
                'session_breakdown': []
            })
        
        # Process each unidentified crop
        assigned_crops = []
        unassigned_crops = []
        session_stats = {}
        
        for crop in unidentified_crops:
            result = AssignmentService.auto_assign(
                crop=crop,
                similarity_threshold=similarity_threshold,
                k=k,
                use_voting=use_voting,
                commit=True  # Auto-commit assignments
            )
            
            # Track per-session statistics
            session_id = crop.image.session.id
            if session_id not in session_stats:
                session_stats[session_id] = {
                    'session_name': crop.image.session.name,
                    'assigned': 0,
                    'unassigned': 0
                }
            
            if result['assigned']:
                assigned_crops.append({
                    'crop_id': crop.id,
                    'student_id': result['student_id'],
                    'student_name': crop.student.full_name if crop.student else None,
                    'confidence': result.get('confidence'),
                    'session_id': session_id,
                    'crop_image_path': request.build_absolute_uri(crop.crop_image_path.url) if crop.crop_image_path else None
                })
                session_stats[session_id]['assigned'] += 1
            else:
                unassigned_crops.append({
                    'crop_id': crop.id,
                    'reason': result.get('message', 'No confident match found'),
                    'session_id': session_id,
                    'crop_image_path': request.build_absolute_uri(crop.crop_image_path.url) if crop.crop_image_path else None
                })
                session_stats[session_id]['unassigned'] += 1
        
        # Format session breakdown
        session_breakdown = [
            {
                'session_id': sid,
                'session_name': stats['session_name'],
                'crops_assigned': stats['assigned'],
                'crops_unassigned': stats['unassigned']
            }
            for sid, stats in session_stats.items()
        ]
        
        return Response({
            'status': 'completed',
            'class_id': class_obj.id,
            'class_name': class_obj.name,
            'parameters': {
                'k': k,
                'similarity_threshold': similarity_threshold,
                'embedding_model': embedding_model,
                'use_voting': use_voting
            },
            'total_crops': all_crops.count(),
            'crops_to_process': total_to_process,
            'crops_assigned': len(assigned_crops),
            'crops_unassigned': len(unassigned_crops),
            'assigned_crops': assigned_crops,
            'unassigned_crops': unassigned_crops,
            'session_breakdown': session_breakdown
        })

    @action(detail=True, methods=['get'], url_path='suggest-assignments')
    def suggest_assignments(self, request, pk=None):
        """
        Get top-k similar faces for all unidentified crops across all sessions in the class.
        This is used for manual assignment workflow where user chooses from suggestions.
        
        Query params:
        - k: Number of similar faces to return per crop (default: 5)
        - embedding_model: Optional model filter
        - include_unidentified: Include unidentified faces in suggestions (default: true)
        - limit: Maximum number of crops to return suggestions for (default: 100)
        
        Returns:
        - List of unidentified crops with their top-k similar faces
        - Progress information (total count, sessions covered)
        """
        from attendance.services import AssignmentService
        
        class_obj = self.get_object()
        
        # Parse parameters
        k = int(request.query_params.get('k', 5))
        embedding_model = request.query_params.get('embedding_model')
        include_unidentified = request.query_params.get('include_unidentified', 'true').lower() == 'true'
        limit = int(request.query_params.get('limit', 100))
        
        # Validate parameters
        if k < 1 or k > 50:
            return Response({'error': 'k must be between 1 and 50'}, status=status.HTTP_400_BAD_REQUEST)
        if limit < 1 or limit > 1000:
            return Response({'error': 'limit must be between 1 and 1000'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get all unidentified crops with embeddings across all sessions
        unidentified_crops = FaceCrop.objects.filter(
            image__session__class_session=class_obj,
            is_identified=False,
            embedding__isnull=False
        ).select_related('image__session')
        
        if embedding_model:
            unidentified_crops = unidentified_crops.filter(embedding_model=embedding_model)
        
        # Limit the number of crops
        total_count = unidentified_crops.count()
        unidentified_crops = unidentified_crops[:limit]
        
        if not unidentified_crops.exists():
            return Response({
                'class_id': class_obj.id,
                'class_name': class_obj.name,
                'total_unidentified': 0,
                'returned_count': 0,
                'suggestions': []
            })
        
        # Get suggestions for each crop
        suggestions = []
        sessions_covered = set()
        
        for crop in unidentified_crops:
            similar_faces = AssignmentService.find_similar_crops(
                crop=crop,
                k=k,
                include_unidentified=include_unidentified
            )
            
            # Convert relative paths to absolute URLs for similar faces
            for sf in similar_faces:
                if sf.get('crop_image_path'):
                    try:
                        neighbor_crop = FaceCrop.objects.get(id=sf['crop_id'])
                        if neighbor_crop.crop_image_path:
                            sf['crop_image_path'] = request.build_absolute_uri(neighbor_crop.crop_image_path.url)
                        else:
                            sf['crop_image_path'] = None
                    except FaceCrop.DoesNotExist:
                        sf['crop_image_path'] = None
            
            sessions_covered.add(crop.image.session.id)
            
            suggestions.append({
                'crop_id': crop.id,
                'crop_image_path': request.build_absolute_uri(crop.crop_image_path.url) if crop.crop_image_path else None,
                'image_id': crop.image.id,
                'session_id': crop.image.session.id,
                'session_name': crop.image.session.name,
                'similar_faces': similar_faces
            })
        
        return Response({
            'class_id': class_obj.id,
            'class_name': class_obj.name,
            'total_unidentified': total_count,
            'returned_count': len(suggestions),
            'sessions_covered': len(sessions_covered),
            'suggestions': suggestions
        })


class StudentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Student model.
    
    Admins: Full CRUD access to all students
    Users: Can create, read, update, delete students in their own classes
    """
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated, IsClassOwnerOrAdmin]
    
    def get_queryset(self):
        """
        Return all students for admin users.
        Return only students from owned classes for regular users.
        """
        user = self.request.user
        if user.is_staff:
            queryset = Student.objects.all()
        else:
            queryset = Student.objects.filter(class_enrolled__owner=user)
        
        # Filter by class if specified
        class_id = self.request.query_params.get('class_id', None)
        if class_id:
            queryset = queryset.filter(class_enrolled_id=class_id)
        
        return queryset.order_by('last_name', 'first_name')
    
    @property
    def paginator(self):
        """
        Override paginator to support custom page_size in query params.
        """
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                from rest_framework.pagination import PageNumberPagination
                
                class CustomPageNumberPagination(PageNumberPagination):
                    page_size = 20
                    page_size_query_param = 'page_size'
                    max_page_size = 10000
                
                self._paginator = CustomPageNumberPagination()
        return self._paginator
    
    def get_serializer_context(self):
        """
        Add request to serializer context for validation.
        """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=True, methods=['get'])
    def attendance(self, request, pk=None):
        """
        Get attendance statistics for a student.
        """
        student = self.get_object()
        
        # Get all sessions in the student's class
        total_sessions = Session.objects.filter(
            class_session=student.class_enrolled
        ).count()
        
        # Get sessions where the student was present
        attended_sessions = Session.objects.filter(
            images__face_crops__student=student
        ).distinct().count()
        
        # Calculate attendance rate
        attendance_rate = (attended_sessions / total_sessions * 100) if total_sessions > 0 else 0
        
        stats = {
            'total_sessions': total_sessions,
            'attended_sessions': attended_sessions,
            'attendance_rate': round(attendance_rate, 2),
            'total_detections': student.face_crops.count(),
        }
        
        return Response(stats)
    
    @action(detail=True, methods=['get'], url_path='detail-report')
    def detail_report(self, request, pk=None):
        """
        Get detailed report for a student including all sessions attended
        and face crops per session.
        """
        student = self.get_object()
        
        # Get all sessions in the student's class ordered by date
        all_sessions = Session.objects.filter(
            class_session=student.class_enrolled
        ).order_by('-date', '-created_at')
        
        # Get sessions where student was present
        attended_session_ids = set(
            Session.objects.filter(
                images__face_crops__student=student
            ).distinct().values_list('id', flat=True)
        )
        
        # Build session attendance details
        session_details = []
        for session in all_sessions:
            # Get face crops for this student in this session
            face_crops = FaceCrop.objects.filter(
                image__session=session,
                student=student
            ).select_related('image')
            
            crops_data = []
            for crop in face_crops:
                # Build absolute URL for crop image
                crop_image_url = ''
                if crop.crop_image_path:
                    crop_image_url = request.build_absolute_uri(crop.crop_image_path.url)
                
                crops_data.append({
                    'id': crop.id,
                    'image_id': crop.image.id,
                    'crop_image_path': crop_image_url,
                    'confidence_score': crop.confidence_score,
                    'created_at': crop.created_at
                })
            
            session_details.append({
                'session_id': session.id,
                'session_name': session.name,
                'date': session.date,
                'start_time': session.start_time,
                'end_time': session.end_time,
                'was_present': session.id in attended_session_ids,
                'detection_count': len(crops_data),
                'face_crops': crops_data
            })
        
        # Calculate statistics
        total_sessions = all_sessions.count()
        attended_count = len(attended_session_ids)
        attendance_rate = (attended_count / total_sessions * 100) if total_sessions > 0 else 0
        
        return Response({
            'student': StudentSerializer(student, context={'request': request}).data,
            'statistics': {
                'total_sessions': total_sessions,
                'attended_sessions': attended_count,
                'missed_sessions': total_sessions - attended_count,
                'attendance_rate': round(attendance_rate, 2),
                'total_detections': student.face_crops.count()
            },
            'sessions': session_details
        })
    
    @action(detail=True, methods=['post'], url_path='merge')
    def merge(self, request, pk=None):
        """
        Merge this student (source) into another student (target).
        
        This endpoint will:
        1. Validate that both students exist and belong to the same class
        2. Transfer all face crops from source student to target student
        3. Delete the source student
        
        Parameters:
        - target_student_id: ID of the student to merge into (required)
        
        Returns:
        - Success message with statistics about transferred face crops
        - Updated target student data
        
        Example:
        POST /api/attendance/students/123/merge/
        {
            "target_student_id": 456
        }
        """
        source_student = self.get_object()
        
        # Validate request data
        serializer = MergeStudentSerializer(
            data=request.data,
            context={'source_student': source_student, 'request': request}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        target_student = serializer.validated_data['target_student']
        
        # Count face crops before merge
        source_crops_count = source_student.face_crops.count()
        target_crops_before = target_student.face_crops.count()
        
        # Perform the merge in a transaction
        from django.db import transaction
        
        try:
            with transaction.atomic():
                # Transfer all face crops from source to target
                face_crops = FaceCrop.objects.filter(student=source_student)
                face_crops.update(student=target_student)
                
                # Store source student info for response
                source_student_info = {
                    'id': source_student.id,
                    'full_name': source_student.full_name,
                    'student_id': source_student.student_id
                }
                
                # Delete the source student
                source_student.delete()
                
                # Refresh target student data
                target_student.refresh_from_db()
                
            # Return success response
            return Response({
                'status': 'success',
                'message': f'Successfully merged students',
                'source_student': source_student_info,
                'target_student': StudentSerializer(target_student, context={'request': request}).data,
                'statistics': {
                    'face_crops_transferred': source_crops_count,
                    'target_crops_before_merge': target_crops_before,
                    'target_crops_after_merge': target_student.face_crops.count()
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {
                    'error': 'Failed to merge students',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(
        detail=True, 
        methods=['post', 'delete'], 
        url_path='profile-picture',
        parser_classes=[MultiPartParser, FormParser]
    )
    def profile_picture(self, request, pk=None):
        """
        Upload or delete a student's profile picture.
        
        POST: Upload a new profile picture
        - Accepts multipart/form-data with 'profile_picture' file field
        - Replaces existing profile picture if one exists
        
        DELETE: Remove the student's profile picture
        
        Returns:
        - Updated student data with profile picture URL
        """
        student = self.get_object()
        
        if request.method == 'DELETE':
            # Delete the profile picture
            if student.profile_picture:
                student.profile_picture.delete(save=False)
                student.profile_picture = None
                student.save(update_fields=['profile_picture'])
            
            serializer = self.get_serializer(student)
            return Response({
                'message': 'Profile picture deleted successfully',
                'student': serializer.data
            }, status=status.HTTP_200_OK)
        
        # POST - Upload new profile picture
        if 'profile_picture' not in request.FILES:
            return Response(
                {'error': 'No profile picture file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        profile_picture = request.FILES['profile_picture']
        
        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        if profile_picture.size > max_size:
            return Response(
                {'error': 'File size too large. Maximum size is 5MB.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        if profile_picture.content_type not in allowed_types:
            return Response(
                {'error': 'Invalid file type. Only JPEG, PNG, GIF, and WebP images are allowed.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Delete old profile picture if exists
        if student.profile_picture:
            student.profile_picture.delete(save=False)
        
        # Save new profile picture
        student.profile_picture = profile_picture
        student.save(update_fields=['profile_picture'])
        
        serializer = self.get_serializer(student)
        return Response({
            'message': 'Profile picture uploaded successfully',
            'student': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(
        detail=True,
        methods=['post'],
        url_path='set-profile-from-crop'
    )
    def set_profile_from_crop(self, request, pk=None):
        """
        Set a student's profile picture from an existing face crop.
        
        POST: Copy face crop image to be the student's profile picture
        - Requires 'face_crop_id' in request data
        - Face crop must belong to this student
        
        Returns:
        - Updated student data with new profile picture URL
        """
        student = self.get_object()
        
        face_crop_id = request.data.get('face_crop_id')
        if not face_crop_id:
            return Response(
                {'error': 'face_crop_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the face crop
        try:
            face_crop = FaceCrop.objects.get(id=face_crop_id)
        except FaceCrop.DoesNotExist:
            return Response(
                {'error': f'Face crop with ID {face_crop_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify the face crop belongs to this student
        if face_crop.student_id != student.id:
            return Response(
                {'error': 'This face crop does not belong to this student'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if face crop has an image file
        if not face_crop.crop_image_path:
            return Response(
                {'error': 'Face crop has no image file'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from django.core.files import File
            from PIL import Image as PILImage
            import io
            
            # Open the face crop image
            crop_image_file = face_crop.crop_image_path
            
            # Delete old profile picture if exists
            if student.profile_picture:
                student.profile_picture.delete(save=False)
            
            # Copy the face crop to profile picture
            # Read the crop image content
            crop_image_file.open('rb')
            image_content = crop_image_file.read()
            crop_image_file.close()
            
            # Create a new file from the content
            import os
            from django.core.files.uploadedfile import InMemoryUploadedFile
            
            # Generate a unique filename
            ext = os.path.splitext(crop_image_file.name)[1]
            filename = f"student_{student.id}_from_crop_{face_crop.id}{ext}"
            
            # Create file object
            image_file = InMemoryUploadedFile(
                io.BytesIO(image_content),
                None,
                filename,
                'image/jpeg',
                len(image_content),
                None
            )
            
            # Save to student profile picture
            student.profile_picture = image_file
            student.save(update_fields=['profile_picture'])
            
            serializer = self.get_serializer(student)
            return Response({
                'message': 'Profile picture set from face crop successfully',
                'student': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to set profile picture from face crop: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Session model.
    
    Admins: Full CRUD access to all sessions
    Users: Can create, read, update, delete sessions in their own classes
    """
    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated, IsClassOwnerOrAdmin]
    
    def get_queryset(self):
        """
        Return all sessions for admin users.
        Return only sessions from owned classes for regular users.
        """
        user = self.request.user
        if user.is_staff:
            queryset = Session.objects.all()
        else:
            queryset = Session.objects.filter(class_session__owner=user)
        
        # Filter by class if specified
        class_id = self.request.query_params.get('class_id', None)
        if class_id:
            queryset = queryset.filter(class_session_id=class_id)
        
        return queryset.order_by('-date', '-created_at')
    
    def get_serializer_context(self):
        """
        Add request to serializer context for validation.
        """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=True, methods=['get'])
    def images(self, request, pk=None):
        """
        Get all images in a session.
        """
        session = self.get_object()
        images = session.images.all().order_by('-upload_date')
        serializer = ImageSerializer(images, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def attendance(self, request, pk=None):
        """
        Get attendance report for a session.
        """
        session = self.get_object()
        
        # Get all students in the class
        all_students = Student.objects.filter(
            class_enrolled=session.class_session
        ).order_by('last_name', 'first_name')
        
        # Get students present in the session
        present_students = Student.objects.filter(
            face_crops__image__session=session
        ).distinct()
        
        present_ids = set(present_students.values_list('id', flat=True))
        
        attendance_data = []
        for student in all_students:
            attendance_data.append({
                'id': student.id,
                'name': student.full_name,
                'student_id': student.student_id,
                'present': student.id in present_ids,
                'detection_count': student.face_crops.filter(
                    image__session=session
                ).count()
            })
        
        return Response({
            'session': SessionSerializer(session).data,
            'total_students': all_students.count(),
            'present_count': len(present_ids),
            'absent_count': all_students.count() - len(present_ids),
            'attendance': attendance_data
        })
    
    @action(detail=True, methods=['get'], url_path='face-crops')
    def face_crops(self, request, pk=None):
        """
        Get all face crops from all images in the session.
        
        This endpoint returns all face crops detected across all images
        in the session, with optional filtering and sorting.
        
        Query Parameters:
        - is_identified: Filter by identification status (true/false)
        - student_id: Filter by specific student ID
        - sort_by: Sort order (name, -name, identified, -identified, created, -created)
        
        Returns:
        - List of face crops with detailed information
        """
        session_obj = self.get_object()
        
        # Get all face crops from images in this session
        crops = FaceCrop.objects.filter(
            image__session=session_obj
        ).select_related('student', 'image')
        
        # Apply filters
        is_identified = request.query_params.get('is_identified')
        if is_identified is not None:
            crops = crops.filter(is_identified=is_identified.lower() == 'true')
        
        student_id = request.query_params.get('student_id')
        if student_id:
            crops = crops.filter(student_id=student_id)
        
        # Apply sorting
        sort_by = request.query_params.get('sort_by', '-created_at')
        
        # Map sort_by to actual field names
        sort_mapping = {
            'name': 'student__last_name',
            '-name': '-student__last_name',
            'identified': 'is_identified',
            '-identified': '-is_identified',
            'created': 'created_at',
            '-created': '-created_at',
        }
        
        if sort_by in sort_mapping:
            sort_by = sort_mapping[sort_by]
        
        # For name sorting, handle None values by using COALESCE-like behavior
        if 'student__last_name' in sort_by:
            # Put unidentified crops at the end when sorting by name
            from django.db.models import Case, When, Value, IntegerField
            crops = crops.annotate(
                has_student=Case(
                    When(student__isnull=False, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField()
                )
            ).order_by('has_student', sort_by)
        else:
            crops = crops.order_by(sort_by)
        
        # Serialize the crops with request context for absolute URLs
        serializer = FaceCropDetailSerializer(crops, many=True, context={'request': request})
        
        return Response({
            'session_id': session_obj.id,
            'session_name': session_obj.name,
            'total_crops': crops.count(),
            'identified_crops': crops.filter(is_identified=True).count(),
            'unidentified_crops': crops.filter(is_identified=False).count(),
            'face_crops': serializer.data
        })
    
    @action(detail=True, methods=['post'], url_path='aggregate-crops')
    def aggregate_crops(self, request, pk=None):
        """
        Aggregate face crops from all images in the session.
        
        This endpoint processes all face crops from the session's images
        and attempts to match them with students in the class. The actual
        matching logic will be implemented later using the core face
        recognition module.
        
        Parameters (optional):
        - similarity_threshold: Threshold for face matching (default: 0.7)
        - auto_assign: Automatically assign high-confidence matches (default: false)
        
        Returns:
        - Aggregation statistics
        - Identified students
        - Unidentified crops count
        """
        session_obj = self.get_object()
        
        # Check if session has any images
        if not session_obj.images.exists():
            return Response(
                {
                    'error': 'Session has no images',
                    'session_id': session_obj.id
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if images are processed
        unprocessed_images = session_obj.images.filter(is_processed=False).count()
        if unprocessed_images > 0:
            return Response(
                {
                    'warning': f'{unprocessed_images} images in session are not yet processed',
                    'session_id': session_obj.id,
                    'total_images': session_obj.images.count(),
                    'processed_images': session_obj.images.filter(is_processed=True).count()
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = AggregateCropsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        similarity_threshold = serializer.validated_data.get('similarity_threshold', 0.7)
        auto_assign = serializer.validated_data.get('auto_assign', False)
        
        # Get all face crops from session
        all_crops = FaceCrop.objects.filter(image__session=session_obj)
        unidentified_crops = all_crops.filter(is_identified=False)
        
        # TODO: Implement actual crop aggregation logic here
        # This is a stub implementation that will be completed later
        # The actual implementation will:
        # 1. Load face embeddings from all crops in the session
        # 2. Cluster similar faces together
        # 3. Match clusters with known students in the class
        # 4. Assign crops to students based on similarity threshold
        # 5. Update FaceCrop records with student assignments
        
        # For now, return statistics without creating any assignments
        identified_students = Student.objects.filter(
            face_crops__image__session=session_obj
        ).distinct()
        
        return Response({
            'status': 'aggregation_completed',
            'session_id': session_obj.id,
            'session_name': session_obj.name,
            'class_id': session_obj.class_session.id,
            'parameters': {
                'similarity_threshold': similarity_threshold,
                'auto_assign': auto_assign
            },
            'statistics': {
                'total_images': session_obj.images.count(),
                'total_crops': all_crops.count(),
                'identified_crops': all_crops.filter(is_identified=True).count(),
                'unidentified_crops': unidentified_crops.count(),
                'identified_students': identified_students.count(),
                'total_students_in_class': session_obj.class_session.students.count()
            },
            'message': 'Crop aggregation completed successfully. '
                      'Note: Full aggregation logic will be implemented with core face recognition module.'
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='generate-embeddings')
    def generate_embeddings(self, request, pk=None):
        """
        Generate embeddings for all face crops in the session.
        
        This endpoint generates embeddings for all face crops in the session.
        If process_unprocessed_images is true and there are unprocessed images,
        it will process them first.
        
        Parameters:
        - model_name: Embedding model ('arcface', 'facenet512') (default: 'arcface')
        - process_unprocessed_images: Process unprocessed images first (default: false)
        - detector_backend: Detector to use if processing images (default: 'retinaface')
        - confidence_threshold: Detection confidence (default: 0.5)
        - apply_background_effect: Apply background effect (default: true)
        
        Returns:
        - Total crops found
        - Embeddings generated
        - Embeddings failed
        - Images processed (if process_unprocessed_images=true)
        """
        from attendance.services import EmbeddingService
        from attendance.utils import process_image_with_face_detection
        from attendance.serializers import BulkGenerateEmbeddingsSerializer
        
        session_obj = self.get_object()
        
        # Validate request data
        serializer = BulkGenerateEmbeddingsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Get parameters
        model_name = serializer.validated_data.get('model_name', 'arcface')
        process_unprocessed = serializer.validated_data.get('process_unprocessed_images', False)
        detector_backend = serializer.validated_data.get('detector_backend', 'retinaface')
        confidence_threshold = serializer.validated_data.get('confidence_threshold', 0.5)
        apply_background_effect = serializer.validated_data.get('apply_background_effect', True)
        
        # Check for unprocessed images
        unprocessed_images = session_obj.images.filter(is_processed=False)
        
        images_processed = 0
        
        if unprocessed_images.exists():
            if not process_unprocessed:
                return Response({
                    'error': 'Session has unprocessed images',
                    'unprocessed_count': unprocessed_images.count(),
                    'message': 'Set process_unprocessed_images=true to process them first'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Process unprocessed images first
            for image in unprocessed_images:
                try:
                    process_image_with_face_detection(
                        image_obj=image,
                        detector_backend=detector_backend,
                        min_confidence=confidence_threshold,
                        apply_background_effect=apply_background_effect,
                        rectangle_color=(0, 255, 0),
                        rectangle_thickness=2
                    )
                    images_processed += 1
                except Exception as e:
                    # Continue processing other images
                    pass
        
        # Get all face crops in the session
        all_face_crops = FaceCrop.objects.filter(image__session=session_obj)
        
        # Only process crops without embeddings
        face_crops = all_face_crops.filter(embedding__isnull=True)
        
        crops_with_embeddings = all_face_crops.filter(embedding__isnull=False).count()
        
        if not face_crops.exists():
            return Response({
                'status': 'completed',
                'message': 'All face crops already have embeddings',
                'total_crops': all_face_crops.count(),
                'crops_with_embeddings': crops_with_embeddings,
                'crops_without_embeddings': 0,
                'embeddings_generated': 0,
                'embeddings_failed': 0,
                'images_processed': images_processed
            })
        
        # Generate embeddings
        generated_count = 0
        failed_count = 0
        errors = []
        
        for crop in face_crops:
            crop_image_path = crop.crop_image_path.path if crop.crop_image_path else None
            
            if not crop_image_path or not os.path.exists(crop_image_path):
                failed_count += 1
                continue
            
            try:
                embedding = EmbeddingService.generate_embedding(
                    image_path=crop_image_path,
                    model_name=model_name
                )
                
                if embedding is not None:
                    crop.embedding = embedding
                    crop.embedding_model = model_name
                    crop.save(update_fields=['embedding', 'embedding_model', 'updated_at'])
                    generated_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                failed_count += 1
                errors.append({
                    'crop_id': crop.id,
                    'error': str(e)
                })
        
        return Response({
            'status': 'completed',
            'session_id': session_obj.id,
            'session_name': session_obj.name,
            'class_id': session_obj.class_session.id,
            'model_name': model_name,
            'total_crops': all_face_crops.count(),
            'crops_with_embeddings': crops_with_embeddings,
            'crops_without_embeddings': face_crops.count(),
            'embeddings_generated': generated_count,
            'embeddings_failed': failed_count,
            'images_processed': images_processed,
            'errors': errors[:10] if errors else None  # Limit to first 10 errors
        })

    @action(detail=True, methods=['post'], url_path='cluster-crops')
    def cluster_crops(self, request, pk=None):
        """
        Cluster face crops in this session based on embedding similarity.
        Creates new Student instances for each cluster and assigns crops.
        
        Constraints:
        - Face crops with existing student assignments are kept in separate clusters
        - Never mixes crops from different students in the same cluster
        - Only unidentified crops are clustered together
        - Only crops with embeddings are processed (crops without embeddings are ignored)
        
        Body params:
        - max_clusters: Maximum number of clusters (2-200)
        - force_clustering: If False, crops with low similarity stay unassigned
        - similarity_threshold: Minimum similarity for clustering (0.0-1.0)
        """
        session_obj = self.get_object()
        
        # Validate request data
        serializer = ClusterCropsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Extract validated parameters
        max_clusters = serializer.validated_data['max_clusters']
        force_clustering = serializer.validated_data['force_clustering']
        similarity_threshold = serializer.validated_data['similarity_threshold']
        
        # Import ClusteringService
        from attendance.services import ClusteringService
        
        try:
            # Run clustering
            result = ClusteringService.cluster_session_crops(
                session_id=session_obj.id,
                max_clusters=max_clusters,
                force_clustering=force_clustering,
                similarity_threshold=similarity_threshold
            )
            
            return Response({
                'status': 'success',
                'session_id': session_obj.id,
                'session_name': session_obj.name,
                **result
            })
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Clustering failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='auto-assign-all-crops')
    def auto_assign_all_crops(self, request, pk=None):
        """
        Automatically assign all unidentified face crops in the session to students
        using similarity-based matching.
        
        This endpoint processes all unidentified crops that have embeddings and attempts
        to assign them to students using K-Nearest Neighbors on existing identified crops.
        
        Body params:
        - k: Number of neighbors to consider (default: 5)
        - similarity_threshold: Minimum similarity score (0.0-1.0, default: 0.6)
        - embedding_model: Optional model filter ('arcface' or 'facenet512')
        - use_voting: Use majority voting among top-k (default: false)
        
        Returns:
        - Statistics about assignments made
        - List of assigned crops with confidence scores
        - List of unassigned crops (with reasons)
        """
        from attendance.services import AssignmentService
        
        session_obj = self.get_object()
        
        # Parse parameters with defaults
        k = int(request.data.get('k', 5))
        similarity_threshold = float(request.data.get('similarity_threshold', 0.6))
        embedding_model = request.data.get('embedding_model')
        use_voting = bool(request.data.get('use_voting', False))
        
        # Validate parameters
        if k < 1 or k > 50:
            return Response({'error': 'k must be between 1 and 50'}, status=status.HTTP_400_BAD_REQUEST)
        if similarity_threshold < 0.0 or similarity_threshold > 1.0:
            return Response({'error': 'similarity_threshold must be between 0.0 and 1.0'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get all face crops in the session
        all_crops = FaceCrop.objects.filter(image__session=session_obj)
        
        # Filter to unidentified crops with embeddings
        unidentified_crops = all_crops.filter(
            is_identified=False,
            embedding__isnull=False
        )
        
        if embedding_model:
            unidentified_crops = unidentified_crops.filter(embedding_model=embedding_model)
        
        total_to_process = unidentified_crops.count()
        
        if total_to_process == 0:
            return Response({
                'status': 'completed',
                'message': 'No unidentified crops with embeddings found',
                'session_id': session_obj.id,
                'session_name': session_obj.name,
                'total_crops': all_crops.count(),
                'crops_to_process': 0,
                'crops_assigned': 0,
                'crops_unassigned': 0,
                'assigned_crops': [],
                'unassigned_crops': []
            })
        
        # Process each unidentified crop
        assigned_crops = []
        unassigned_crops = []
        
        for crop in unidentified_crops:
            result = AssignmentService.auto_assign(
                crop=crop,
                similarity_threshold=similarity_threshold,
                k=k,
                use_voting=use_voting,
                commit=True  # Auto-commit assignments
            )
            
            if result['assigned']:
                assigned_crops.append({
                    'crop_id': crop.id,
                    'student_id': result['student_id'],
                    'student_name': crop.student.full_name if crop.student else None,
                    'confidence': result.get('confidence'),
                    'crop_image_path': request.build_absolute_uri(crop.crop_image_path.url) if crop.crop_image_path else None
                })
            else:
                unassigned_crops.append({
                    'crop_id': crop.id,
                    'reason': result.get('message', 'No confident match found'),
                    'crop_image_path': request.build_absolute_uri(crop.crop_image_path.url) if crop.crop_image_path else None
                })
        
        return Response({
            'status': 'completed',
            'session_id': session_obj.id,
            'session_name': session_obj.name,
            'class_id': session_obj.class_session.id,
            'parameters': {
                'k': k,
                'similarity_threshold': similarity_threshold,
                'embedding_model': embedding_model,
                'use_voting': use_voting
            },
            'total_crops': all_crops.count(),
            'crops_to_process': total_to_process,
            'crops_assigned': len(assigned_crops),
            'crops_unassigned': len(unassigned_crops),
            'assigned_crops': assigned_crops,
            'unassigned_crops': unassigned_crops
        })

    @action(detail=True, methods=['get'], url_path='suggest-assignments')
    def suggest_assignments(self, request, pk=None):
        """
        Get top-k similar faces for all unidentified crops in the session.
        This is used for manual assignment workflow where user chooses from suggestions.
        
        Query params:
        - k: Number of similar faces to return per crop (default: 5)
        - embedding_model: Optional model filter
        - include_unidentified: Include unidentified faces in suggestions (default: true)
        
        Returns:
        - List of unidentified crops with their top-k similar faces
        - Progress information (current position, total count)
        """
        from attendance.services import AssignmentService
        
        session_obj = self.get_object()
        
        # Parse parameters
        k = int(request.query_params.get('k', 5))
        embedding_model = request.query_params.get('embedding_model')
        include_unidentified = request.query_params.get('include_unidentified', 'true').lower() == 'true'
        
        # Validate parameters
        if k < 1 or k > 50:
            return Response({'error': 'k must be between 1 and 50'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get all unidentified crops with embeddings
        unidentified_crops = FaceCrop.objects.filter(
            image__session=session_obj,
            is_identified=False,
            embedding__isnull=False
        )
        
        if embedding_model:
            unidentified_crops = unidentified_crops.filter(embedding_model=embedding_model)
        
        # Get suggestions for each crop
        suggestions_data = []
        for crop in unidentified_crops:
            neighbors = AssignmentService.find_similar_crops(
                crop=crop,
                k=k,
                embedding_model=embedding_model or crop.embedding_model,
                include_unidentified=include_unidentified
            )
            
            # Convert relative paths to absolute URLs
            for neighbor in neighbors:
                if neighbor.get('crop_image_path'):
                    try:
                        neighbor_crop = FaceCrop.objects.get(id=neighbor['crop_id'])
                        if neighbor_crop.crop_image_path:
                            neighbor['crop_image_path'] = request.build_absolute_uri(neighbor_crop.crop_image_path.url)
                    except FaceCrop.DoesNotExist:
                        pass
            
            suggestions_data.append({
                'crop_id': crop.id,
                'crop_image_path': request.build_absolute_uri(crop.crop_image_path.url) if crop.crop_image_path else None,
                'image_id': crop.image_id,
                'similar_faces': neighbors
            })
        
        return Response({
            'session_id': session_obj.id,
            'session_name': session_obj.name,
            'total_crops': unidentified_crops.count(),
            'parameters': {
                'k': k,
                'embedding_model': embedding_model,
                'include_unidentified': include_unidentified
            },
            'suggestions': suggestions_data
        })


class ImageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Image model.
    
    Admins: Full CRUD access to all images
    Users: Can create, read, delete images in their own sessions
    Update is limited to processed_image_path
    """
    serializer_class = ImageSerializer
    permission_classes = [IsAuthenticated, IsClassOwnerOrAdmin]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']
    # Accept JSON for actions like process-image, and multipart for create
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get_queryset(self):
        """
        Return all images for admin users.
        Return only images from owned classes for regular users.
        """
        user = self.request.user
        if user.is_staff:
            queryset = Image.objects.all()
        else:
            queryset = Image.objects.filter(session__class_session__owner=user)
        
        # Filter by session if specified
        session_id = self.request.query_params.get('session_id', None)
        if session_id:
            queryset = queryset.filter(session_id=session_id)
        
        # Filter by processing status
        is_processed = self.request.query_params.get('is_processed', None)
        if is_processed is not None:
            queryset = queryset.filter(is_processed=is_processed.lower() == 'true')
        
        return queryset.order_by('-upload_date')
    
    def get_serializer_context(self):
        """
        Add request to serializer context for validation.
        """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_serializer_class(self):
        """
        Use a dedicated serializer for create to accept multipart file uploads.
        """
        from .serializers import ImageCreateSerializer, ImageSerializer as ReadSerializer
        if self.action == 'create':
            return ImageCreateSerializer
        return ReadSerializer

    def create(self, request, *args, **kwargs):
        """
        Override create to return the read serializer payload with absolute URLs
        after saving the uploaded file.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        image = serializer.save()
        # Re-serialize with read serializer for URL fields
        read_serializer = ImageSerializer(image, context={'request': request})
        headers = self.get_success_headers(read_serializer.data)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=True, methods=['get'])
    def face_crops(self, request, pk=None):
        """
        Get all face crops in an image.
        """
        image = self.get_object()
        crops = image.face_crops.all().order_by('-created_at')
        serializer = FaceCropDetailSerializer(crops, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_processed(self, request, pk=None):
        """
        Mark an image as processed.
        """
        image = self.get_object()
        processed_path = request.data.get('processed_image_path')
        
        if not processed_path:
            return Response(
                {'error': 'processed_image_path is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        image.mark_as_processed(processed_path)
        serializer = self.get_serializer(image)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='process-image')
    def process_image(self, request, pk=None):
        """
        Process an image to extract face crops.
        
        This endpoint triggers the face detection and extraction process
        on the uploaded image using the core face recognition module.
        
        Parameters (optional):
        - min_face_size: Minimum face size in pixels (default: 20)
        - confidence_threshold: Confidence threshold for detection (default: 0.5)
        
        Returns:
        - Processing status
        - Number of faces detected
        - List of created face crops
        """
        from attendance.utils import process_image_with_face_detection
        
        image_obj = self.get_object()
        
        # Check if image is already processed
        if image_obj.is_processed:
            return Response(
                {
                    'error': 'Image has already been processed',
                    'image_id': image_obj.id,
                    'processed_date': image_obj.processing_date
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ProcessImageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract parameters from validated data
        detector_backend = serializer.validated_data.get('detector_backend', 'retinaface')
        min_confidence = serializer.validated_data.get('confidence_threshold', 0.0)
        apply_background_effect = serializer.validated_data.get('apply_background_effect', True)
        rectangle_color = tuple(serializer.validated_data.get('rectangle_color', [0, 255, 0]))
        rectangle_thickness = serializer.validated_data.get('rectangle_thickness', 2)
        
        try:
            # Process the image and extract face crops
            result = process_image_with_face_detection(
                image_obj=image_obj,
                detector_backend=detector_backend,
                min_confidence=min_confidence,
                apply_background_effect=apply_background_effect,
                rectangle_color=rectangle_color,
                rectangle_thickness=rectangle_thickness
            )
            
            return Response({
                'status': 'completed',
                'image_id': image_obj.id,
                'session_id': image_obj.session.id,
                'class_id': image_obj.session.class_session.id,
                'faces_detected': result['faces_detected'],
                'crops_created': result['crops_created'],
                'processed_image_url': result['processed_image_url'],
                'message': 'Image processed successfully'
            })
        
        except FileNotFoundError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {
                    'error': 'Failed to process image',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FaceCropViewSet(viewsets.ModelViewSet):
    """
    ViewSet for FaceCrop model.
    
    Admins: Full CRUD access to all face crops
    Users: Can only update the student field for crops in their own classes
    Read and list access for crops in their own classes
    DELETE is allowed to remove unwanted face crops
    """
    permission_classes = [IsAuthenticated, IsClassOwnerOrAdmin]
    http_method_names = ['get', 'patch', 'post', 'delete', 'head', 'options']
    
    def get_serializer_class(self):
        """
        Use detailed serializer for retrieve action.
        """
        if self.action == 'retrieve':
            return FaceCropDetailSerializer
        return FaceCropSerializer
    
    def get_queryset(self):
        """
        Return all face crops for admin users.
        Return only face crops from owned classes for regular users.
        """
        user = self.request.user
        if user.is_staff:
            queryset = FaceCrop.objects.all()
        else:
            queryset = FaceCrop.objects.filter(
                image__session__class_session__owner=user
            )
        
        # Filter by image if specified
        image_id = self.request.query_params.get('image_id', None)
        if image_id:
            queryset = queryset.filter(image_id=image_id)
        
        # Filter by session if specified
        session_id = self.request.query_params.get('session_id', None)
        if session_id:
            queryset = queryset.filter(image__session_id=session_id)
        
        # Filter by identification status
        is_identified = self.request.query_params.get('is_identified', None)
        if is_identified is not None:
            queryset = queryset.filter(is_identified=is_identified.lower() == 'true')
        
        # Filter by student
        student_id = self.request.query_params.get('student_id', None)
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        return queryset.order_by('-created_at')
    
    def get_serializer_context(self):
        """
        Add request to serializer context for validation.
        """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=True, methods=['post'])
    def unidentify(self, request, pk=None):
        """
        Clear the student assignment for a face crop.
        """
        crop = self.get_object()
        crop.student = None
        crop.is_identified = False
        crop.save()
        
        serializer = self.get_serializer(crop)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='generate-embedding')
    def generate_embedding(self, request, pk=None):
        """
        Generate face embedding for a face crop.
        
        This endpoint generates a face embedding vector using DeepFace
        and saves it to the face crop model along with the model name.
        
        Parameters:
    - model_name: Model to use ('arcface' or 'facenet512')
                     Default: 'arcface'
        
        Returns:
        - Updated face crop with embedding information
        - Embedding dimension
        - Model used
        
        Example:
        POST /api/attendance/face-crops/123/generate-embedding/
        {
            "model_name": "arcface"
        }
        """
        from attendance.services import EmbeddingService
        
        face_crop = self.get_object()
        
        # Validate request data
        serializer = GenerateEmbeddingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        model_name = serializer.validated_data.get('model_name', 'arcface')
        
        # Get the full path to the face crop image
        crop_image_path = face_crop.crop_image_path.path if face_crop.crop_image_path else None
        
        if not crop_image_path or not os.path.exists(crop_image_path):
            return Response(
                {'error': 'Face crop image not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Generate embedding
            embedding = EmbeddingService.generate_embedding(
                image_path=crop_image_path,
                model_name=model_name
            )
            
            if embedding is None:
                return Response(
                    {'error': 'Failed to generate embedding. No face detected in crop.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save embedding to the face crop
            face_crop.embedding = embedding
            face_crop.embedding_model = model_name
            face_crop.save(update_fields=['embedding', 'embedding_model', 'updated_at'])
            
            # Get embedding dimension
            embedding_dim = EmbeddingService.get_embedding_dimension(model_name)
            
            return Response({
                'status': 'success',
                'message': 'Embedding generated successfully',
                'face_crop_id': face_crop.id,
                'model_name': model_name,
                'embedding_dimension': embedding_dim,
                'embedding_preview': embedding[:5] if len(embedding) > 5 else embedding,  # Show first 5 values
                'has_embedding': face_crop.embedding is not None
            }, status=status.HTTP_200_OK)
            
        except FileNotFoundError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {
                    'error': 'Failed to generate embedding',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='similar-faces')
    def similar_faces(self, request, pk=None):
        """
        Return top-k similar face crops within the same class.

        Query params:
        - k: number of neighbors (default 5)
        - include_unidentified: whether to include crops without student (default true)
        - embedding_model: optional override of embedding model filter
        """
        from attendance.services import AssignmentService

        face_crop = self.get_object()
        if face_crop.embedding is None:
            return Response(
                {'error': 'This crop has no embedding. Generate embedding first.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            k = int(request.query_params.get('k', '5'))
            include_unidentified = request.query_params.get('include_unidentified', 'true').lower() == 'true'
            embedding_model = request.query_params.get('embedding_model') or face_crop.embedding_model
        except ValueError:
            return Response({'error': 'Invalid query parameters'}, status=status.HTTP_400_BAD_REQUEST)

        neighbors = AssignmentService.find_similar_crops(
            crop=face_crop,
            k=max(1, min(50, k)),
            embedding_model=embedding_model,
            include_unidentified=include_unidentified,
        )

        # Convert crop_image_path to absolute URLs
        for neighbor in neighbors:
            if neighbor.get('crop_image_path'):
                try:
                    # Get the crop object to access the ImageField
                    neighbor_crop = FaceCrop.objects.get(id=neighbor['crop_id'])
                    if neighbor_crop.crop_image_path:
                        neighbor['crop_image_path'] = request.build_absolute_uri(neighbor_crop.crop_image_path.url)
                except FaceCrop.DoesNotExist:
                    pass

        return Response({
            'crop_id': face_crop.id,
            'k': len(neighbors),
            'embedding_model': embedding_model,
            'neighbors': neighbors,
        })

    @action(detail=True, methods=['post'], url_path='assign')
    def assign(self, request, pk=None):
        """
        Automatically assign this face crop to a student using similarity search.

        Body params:
        - k (int, default 5): number of neighbors to consider when use_voting is true
        - similarity_threshold (float, default 0.6): minimum similarity to accept
        - embedding_model (str, optional): model to use/require
        - use_voting (bool, default false): majority voting over top-k
        - auto_commit (bool, default true): if true, save assignment
        """
        from attendance.services import AssignmentService

        face_crop = self.get_object()

        k = int(request.data.get('k', 5))
        similarity_threshold = float(request.data.get('similarity_threshold', 0.6))
        use_voting = bool(request.data.get('use_voting', False))
        auto_commit = bool(request.data.get('auto_commit', True))
        embedding_model = request.data.get('embedding_model') or face_crop.embedding_model

        if face_crop.embedding is None:
            return Response(
                {'error': 'This crop has no embedding. Generate embedding first.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Optionally enforce embedding model consistency
        if embedding_model and face_crop.embedding_model and embedding_model != face_crop.embedding_model:
            # Not a hard error, but warn in message
            pass

        result = AssignmentService.auto_assign(
            crop=face_crop,
            similarity_threshold=similarity_threshold,
            k=max(1, min(50, k)),
            use_voting=use_voting,
            commit=auto_commit,
        )

        response = {
            'status': 'assigned' if result.get('assigned') else 'no_match',
            'crop_id': face_crop.id,
            'assigned': result.get('assigned', False),
            'student_id': result.get('student_id'),
            'student_name': None,
            'confidence': result.get('confidence'),
            'message': result.get('message', ''),
        }

        if response['student_id']:
            try:
                student = Student.objects.get(id=response['student_id'])
                response['student_name'] = student.full_name
            except Student.DoesNotExist:
                response['student_name'] = None

        # Include neighbors for UI when not committing or for transparency
        response['k_nearest'] = result.get('neighbors', [])

        return Response(response)

    @action(detail=True, methods=['post'], url_path='assign-from-candidate')
    def assign_from_candidate(self, request, pk=None):
        """
        Assign this crop to the same student as a selected candidate crop.

        Body params:
        - candidate_crop_id (int, required)
        - confidence (float, optional): confidence score to store
        """
        from attendance.services import AssignmentService

        face_crop = self.get_object()
        candidate_crop_id = request.data.get('candidate_crop_id')
        confidence = request.data.get('confidence')
        try:
            confidence_val = float(confidence) if confidence is not None else None
        except (TypeError, ValueError):
            confidence_val = None

        if not candidate_crop_id:
            return Response({'error': 'candidate_crop_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            candidate_id_int = int(candidate_crop_id)
        except (TypeError, ValueError):
            return Response({'error': 'candidate_crop_id must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

        result = AssignmentService.assign_from_candidate(face_crop, candidate_id_int, confidence_val)
        status_str = 'assigned' if result.get('assigned') else 'no_assignment'
        return Response({
            'status': status_str,
            'crop_id': face_crop.id,
            'assigned': result.get('assigned', False),
            'student_id': result.get('student_id'),
            'student_name': result.get('student_name'),
            'confidence': result.get('confidence'),
            'message': result.get('message'),
        })

    @action(detail=True, methods=['post'], url_path='create-and-assign-student')
    def create_and_assign_student(self, request, pk=None):
        """
        Create a new student with a default name and assign this face crop to them.
        
        Body params:
        - class_id (int, required): The class to create the student in
        - confidence (float, optional): confidence score to store
        """
        face_crop = self.get_object()
        class_id = request.data.get('class_id')
        confidence = request.data.get('confidence')
        
        if not class_id:
            return Response({'error': 'class_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            class_id_int = int(class_id)
        except (TypeError, ValueError):
            return Response({'error': 'class_id must be an integer'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            confidence_val = float(confidence) if confidence is not None else None
        except (TypeError, ValueError):
            confidence_val = None
        
        # Check that the user has permission to add students to this class
        try:
            class_obj = Class.objects.get(id=class_id_int)
        except Class.DoesNotExist:
            return Response({'error': 'Class not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Permission check: user must own the class (or be admin)
        if not request.user.is_staff and class_obj.owner != request.user:
            return Response(
                {'error': 'You do not have permission to add students to this class'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generate a unique default name for the student
        # Find the next available number
        existing_students = Student.objects.filter(class_enrolled=class_obj)
        counter = 1
        while True:
            first_name = f"Student"
            last_name = f"#{counter}"
            # Check if this name already exists
            if not existing_students.filter(first_name=first_name, last_name=last_name).exists():
                break
            counter += 1
        
        # Create the student
        try:
            student = Student.objects.create(
                class_enrolled=class_obj,
                first_name=first_name,
                last_name=last_name,
                student_id='',
                email=''
            )
        except Exception as e:
            return Response({'error': f'Failed to create student: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Assign the face crop to the new student
        face_crop.identify_student(student, confidence_val)
        
        return Response({
            'status': 'success',
            'crop_id': face_crop.id,
            'assigned': True,
            'student_id': student.id,
            'student_name': student.full_name,
            'student': {
                'id': student.id,
                'class_enrolled': student.class_enrolled.id,
                'class_name': student.class_enrolled.name,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'full_name': student.full_name,
                'student_id': student.student_id,
                'email': student.email,
                'created_at': student.created_at.isoformat(),
            },
            'confidence': confidence_val,
            'message': f'Created new student "{student.full_name}" and assigned face crop',
        })

