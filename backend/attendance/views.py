from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Count, Q
from django.utils import timezone
import os
from .models import Class, Student, Session, Image, FaceCrop
from .serializers import (
    ClassSerializer, StudentSerializer, SessionSerializer,
    ImageSerializer, FaceCropSerializer, FaceCropDetailSerializer,
    BulkStudentUploadSerializer, ProcessImageSerializer,
    AggregateCropsSerializer, AggregateClassSerializer, MergeStudentSerializer
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
        
        stats = {
            'student_count': class_obj.students.count(),
            'session_count': class_obj.sessions.count(),
            'total_images': Image.objects.filter(session__class_session=class_obj).count(),
            'processed_images': Image.objects.filter(
                session__class_session=class_obj,
                is_processed=True
            ).count(),
            'total_face_crops': FaceCrop.objects.filter(
                image__session__class_session=class_obj
            ).count(),
            'identified_faces': FaceCrop.objects.filter(
                image__session__class_session=class_obj,
                is_identified=True
            ).count(),
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
    
    @action(detail=True, methods=['post'], url_path='cluster-crops')
    def cluster_crops(self, request, pk=None):
        """
        Cluster all face crops across all sessions in a class.
        
        This endpoint groups similar faces together across the entire class
        and optionally creates Student records for each cluster.
        
        Parameters:
        - max_clusters: Maximum number of clusters (default: 50)
        - similarity_threshold: Threshold for grouping (default: 0.5)
        - embedding_model: Model to use ('facenet' or 'arcface')
        - create_students: Create Student records for clusters (default: true)
        - assign_crops: Assign crops to created students (default: true)
        - include_identified: Include already identified crops (default: false)
        
        Returns:
        - Clustering results with statistics
        """
        from attendance.services import FaceCropClusteringService
        from attendance.serializers import ClusterFaceCropsSerializer
        
        class_obj = self.get_object()
        
        serializer = ClusterFaceCropsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        max_clusters = serializer.validated_data.get('max_clusters', 50)
        similarity_threshold = serializer.validated_data.get('similarity_threshold', 0.5)
        embedding_model = serializer.validated_data.get('embedding_model', 'facenet')
        create_students = serializer.validated_data.get('create_students', True)
        assign_crops = serializer.validated_data.get('assign_crops', True)
        include_identified = serializer.validated_data.get('include_identified', False)
        
        try:
            clustering_service = FaceCropClusteringService(
                embedding_model=embedding_model,
                max_clusters=max_clusters,
                similarity_threshold=similarity_threshold
            )
            
            result = clustering_service.cluster_class_crops(
                class_id=class_obj.id,
                create_students=create_students,
                assign_crops=assign_crops,
                include_identified=include_identified
            )
            
            return Response(result)
        
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {
                    'error': 'Clustering failed',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='assign-crops')
    def assign_crops_batch(self, request, pk=None):
        """
        Assign all unidentified face crops in a class to students using KNN.
        
        This processes all unidentified crops across all sessions in the class.
        
        Parameters:
        - k: Number of nearest neighbors (default: 5)
        - similarity_threshold: Minimum similarity (default: 0.6)
        - embedding_model: Model to use ('facenet' or 'arcface')
        - use_voting: Use majority voting (default: true)
        - auto_commit: Save assignments to database (default: true)
        
        Returns:
        - Batch assignment results with statistics
        """
        from attendance.services import FaceCropAssignmentService
        from attendance.serializers import AssignFaceCropSerializer
        
        class_obj = self.get_object()
        
        serializer = AssignFaceCropSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        k = serializer.validated_data.get('k', 5)
        similarity_threshold = serializer.validated_data.get('similarity_threshold', 0.6)
        embedding_model = serializer.validated_data.get('embedding_model', 'facenet')
        use_voting = serializer.validated_data.get('use_voting', True)
        auto_commit = serializer.validated_data.get('auto_commit', True)
        
        try:
            assignment_service = FaceCropAssignmentService(
                embedding_model=embedding_model,
                k=k,
                similarity_threshold=similarity_threshold,
                use_voting=use_voting
            )
            
            result = assignment_service.assign_class_crops(
                class_id=class_obj.id,
                auto_commit=auto_commit
            )
            
            return Response(result)
        
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {
                    'error': 'Assignment failed',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
                crops_data.append({
                    'id': crop.id,
                    'image_id': crop.image.id,
                    'crop_image_path': str(crop.crop_image_path) if crop.crop_image_path else '',
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
        serializer = ImageSerializer(images, many=True)
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
        
        # Serialize the crops
        serializer = FaceCropDetailSerializer(crops, many=True)
        
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
    
    @action(detail=True, methods=['post'], url_path='cluster-crops')
    def cluster_crops(self, request, pk=None):
        """
        Cluster face crops in a session using embeddings.
        
        This endpoint groups similar faces together and optionally creates
        Student records for each cluster.
        
        Parameters:
        - max_clusters: Maximum number of clusters (default: 50)
        - similarity_threshold: Threshold for grouping (default: 0.5)
        - embedding_model: Model to use ('facenet' or 'arcface')
        - create_students: Create Student records for clusters (default: true)
        - assign_crops: Assign crops to created students (default: true)
        
        Returns:
        - Clustering results with statistics
        """
        from attendance.services import FaceCropClusteringService
        from attendance.serializers import ClusterFaceCropsSerializer
        
        session_obj = self.get_object()
        
        serializer = ClusterFaceCropsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        max_clusters = serializer.validated_data.get('max_clusters', 50)
        similarity_threshold = serializer.validated_data.get('similarity_threshold', 0.5)
        embedding_model = serializer.validated_data.get('embedding_model', 'facenet')
        create_students = serializer.validated_data.get('create_students', True)
        assign_crops = serializer.validated_data.get('assign_crops', True)
        
        try:
            clustering_service = FaceCropClusteringService(
                embedding_model=embedding_model,
                max_clusters=max_clusters,
                similarity_threshold=similarity_threshold
            )
            
            result = clustering_service.cluster_session_crops(
                session_id=session_obj.id,
                create_students=create_students,
                assign_crops=assign_crops
            )
            
            return Response(result)
        
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {
                    'error': 'Clustering failed',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='assign-crops')
    def assign_crops_batch(self, request, pk=None):
        """
        Assign all unidentified face crops in a session to students using KNN.
        
        Parameters:
        - k: Number of nearest neighbors (default: 5)
        - similarity_threshold: Minimum similarity (default: 0.6)
        - embedding_model: Model to use ('facenet' or 'arcface')
        - use_voting: Use majority voting (default: true)
        - auto_commit: Save assignments to database (default: true)
        
        Returns:
        - Batch assignment results with statistics
        """
        from attendance.services import FaceCropAssignmentService
        from attendance.serializers import AssignFaceCropSerializer
        
        session_obj = self.get_object()
        
        serializer = AssignFaceCropSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        k = serializer.validated_data.get('k', 5)
        similarity_threshold = serializer.validated_data.get('similarity_threshold', 0.6)
        embedding_model = serializer.validated_data.get('embedding_model', 'facenet')
        use_voting = serializer.validated_data.get('use_voting', True)
        auto_commit = serializer.validated_data.get('auto_commit', True)
        
        try:
            assignment_service = FaceCropAssignmentService(
                embedding_model=embedding_model,
                k=k,
                similarity_threshold=similarity_threshold,
                use_voting=use_voting
            )
            
            result = assignment_service.assign_session_crops(
                session_id=session_obj.id,
                auto_commit=auto_commit
            )
            
            return Response(result)
        
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {
                    'error': 'Assignment failed',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
    
    @action(detail=True, methods=['get'])
    def face_crops(self, request, pk=None):
        """
        Get all face crops in an image.
        """
        image = self.get_object()
        crops = image.face_crops.all().order_by('-created_at')
        serializer = FaceCropDetailSerializer(crops, many=True)
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
        Generate embedding for a single face crop.
        
        Parameters:
        - model_name: Embedding model to use ('facenet' or 'arcface')
        - force_regenerate: Force regeneration even if exists
        
        Returns:
        - Embedding generation status and info
        """
        from attendance.services import EmbeddingService
        from attendance.serializers import GenerateEmbeddingSerializer
        import logging
        import gc
        import time
        
        logger = logging.getLogger(__name__)
        crop = self.get_object()
        
        serializer = GenerateEmbeddingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        model_name = serializer.validated_data.get('model_name', 'facenet')
        force_regenerate = serializer.validated_data.get('force_regenerate', False)
        
        logger.info(f"Generating embedding for crop {crop.id} using {model_name}")
        
        # Check if embedding already exists
        # Use 'is not None' to avoid ambiguous truth value error with arrays
        if not force_regenerate and crop.embedding is not None and crop.embedding_model == model_name:
            logger.info(f"Embedding already exists for crop {crop.id}, skipping generation")
            return Response({
                'status': 'already_exists',
                'crop_id': crop.id,
                'embedding_model': crop.embedding_model,
                'embedding_dimension': len(crop.embedding),
                'message': 'Embedding already exists'
            })
        
        embedding_service = None
        try:
            # Verify file exists before processing
            crop_path = crop.crop_image_path.path
            if not os.path.exists(crop_path):
                logger.error(f"Crop image file not found: {crop_path}")
                return Response(
                    {'error': f'Crop image file not found: {crop_path}'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            logger.info(f"Processing crop image at: {crop_path}")
            
            # Generate embedding
            embedding_service = EmbeddingService(model_name=model_name)
            embedding_obj = embedding_service.generate_embedding(crop_path)
            
            # Convert to list for database storage
            embedding_list = embedding_obj.vector.tolist()
            
            # Save to database
            crop.embedding = embedding_list
            crop.embedding_model = model_name
            crop.save(update_fields=['embedding', 'embedding_model', 'updated_at'])
            
            logger.info(f"Successfully generated {embedding_obj.dimension}D embedding for crop {crop.id}")
            
            # Clean up
            del embedding_obj
            del embedding_list
            gc.collect()
            
            # Small delay to allow TensorFlow to fully clean up
            time.sleep(0.1)
            
            return Response({
                'status': 'success',
                'crop_id': crop.id,
                'embedding_model': model_name,
                'embedding_dimension': embedding_obj.dimension if 'embedding_obj' in locals() else len(crop.embedding),
                'message': 'Embedding generated successfully'
            })
        
        except FileNotFoundError as e:
            logger.error(f"File not found for crop {crop.id}: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            logger.error(f"Value error generating embedding for crop {crop.id}: {str(e)}")
            return Response(
                {
                    'error': 'Invalid crop image or model configuration',
                    'details': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Failed to generate embedding for crop {crop.id}: {str(e)}", exc_info=True)
            return Response(
                {
                    'error': 'Failed to generate embedding',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            # Force cleanup
            if embedding_service:
                del embedding_service
            gc.collect()
    
    @action(detail=False, methods=['post'], url_path='generate-embeddings-batch')
    def generate_embeddings_batch(self, request):
        """
        Generate embeddings for multiple face crops.
        
        Parameters:
        - face_crop_ids: List of FaceCrop IDs
        - model_name: Embedding model to use
        - force_regenerate: Force regeneration even if exists
        
        Returns:
        - Batch generation results
        """
        from attendance.services import EmbeddingService
        from attendance.serializers import GenerateEmbeddingSerializer
        
        serializer = GenerateEmbeddingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        face_crop_ids = serializer.validated_data.get('face_crop_ids', [])
        model_name = serializer.validated_data.get('model_name', 'facenet')
        force_regenerate = serializer.validated_data.get('force_regenerate', False)
        
        if not face_crop_ids:
            return Response(
                {'error': 'face_crop_ids is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get face crops
        crops = FaceCrop.objects.filter(id__in=face_crop_ids)
        
        if not crops.exists():
            return Response(
                {'error': 'No face crops found with provided IDs'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Generate embeddings
        embedding_service = EmbeddingService(model_name=model_name)
        results = []
        success_count = 0
        skipped_count = 0
        error_count = 0
        
        for crop in crops:
            # Check if already exists
            # Use 'is not None' to avoid ambiguous truth value error with arrays
            if not force_regenerate and crop.embedding is not None and crop.embedding_model == model_name:
                results.append({
                    'crop_id': crop.id,
                    'status': 'skipped',
                    'message': 'Embedding already exists'
                })
                skipped_count += 1
                continue
            
            try:
                crop_path = crop.crop_image_path.path
                embedding_obj = embedding_service.generate_embedding(crop_path)
                
                crop.embedding = embedding_obj.vector.tolist()
                crop.embedding_model = model_name
                crop.save(update_fields=['embedding', 'embedding_model', 'updated_at'])
                
                results.append({
                    'crop_id': crop.id,
                    'status': 'success',
                    'embedding_dimension': embedding_obj.dimension
                })
                success_count += 1
            
            except Exception as e:
                results.append({
                    'crop_id': crop.id,
                    'status': 'error',
                    'error': str(e)
                })
                error_count += 1
        
        return Response({
            'status': 'completed',
            'total': len(face_crop_ids),
            'success': success_count,
            'skipped': skipped_count,
            'errors': error_count,
            'model_name': model_name,
            'results': results
        })
    
    @action(detail=True, methods=['post'], url_path='assign')
    def assign_crop(self, request, pk=None):
        """
        Assign a face crop to a student using KNN similarity search.
        
        Parameters:
        - k: Number of nearest neighbors
        - similarity_threshold: Minimum similarity for assignment
        - embedding_model: Model to use for embeddings
        - use_voting: Use majority voting in KNN
        - auto_commit: Save assignment to database
        
        Returns:
        - Assignment result with student info and confidence
        """
        from attendance.services import FaceCropAssignmentService
        from attendance.serializers import AssignFaceCropSerializer
        
        crop = self.get_object()
        
        serializer = AssignFaceCropSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        k = serializer.validated_data.get('k', 5)
        similarity_threshold = serializer.validated_data.get('similarity_threshold', 0.6)
        embedding_model = serializer.validated_data.get('embedding_model', 'facenet')
        use_voting = serializer.validated_data.get('use_voting', True)
        auto_commit = serializer.validated_data.get('auto_commit', True)
        
        try:
            assignment_service = FaceCropAssignmentService(
                embedding_model=embedding_model,
                k=k,
                similarity_threshold=similarity_threshold,
                use_voting=use_voting
            )
            
            result = assignment_service.assign_crop(
                crop_id=crop.id,
                auto_commit=auto_commit
            )
            
            return Response(result)
        
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {
                    'error': 'Assignment failed',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
