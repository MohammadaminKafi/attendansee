from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Count, Q
from django.utils import timezone
from .models import Class, Student, Session, Image, FaceCrop
from .serializers import (
    ClassSerializer, StudentSerializer, SessionSerializer,
    ImageSerializer, FaceCropSerializer, FaceCropDetailSerializer,
    BulkStudentUploadSerializer, ProcessImageSerializer,
    AggregateCropsSerializer, AggregateClassSerializer
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
        on the uploaded image. The actual processing logic will be
        implemented later using the core face recognition module.
        
        Parameters (optional):
        - min_face_size: Minimum face size in pixels (default: 20)
        - confidence_threshold: Confidence threshold for detection (default: 0.5)
        
        Returns:
        - Processing status
        - Number of faces detected
        - List of created face crops
        """
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
        
        min_face_size = serializer.validated_data.get('min_face_size', 20)
        confidence_threshold = serializer.validated_data.get('confidence_threshold', 0.5)
        
        # TODO: Implement actual face detection and extraction here
        # This is a stub implementation that will be completed later
        # The actual implementation will:
        # 1. Load the image from original_image_path
        # 2. Run face detection using the core face module
        # 3. Extract face crops for each detected face
        # 4. Save crops to disk
        # 5. Create FaceCrop objects with coordinates and paths
        # 6. Mark image as processed
        
        # For now, return a stub response
        return Response({
            'status': 'processing_queued',
            'image_id': image_obj.id,
            'session_id': image_obj.session.id,
            'class_id': image_obj.session.class_session.id,
            'parameters': {
                'min_face_size': min_face_size,
                'confidence_threshold': confidence_threshold
            },
            'faces_detected': 0,
            'crops_created': [],
            'message': 'Image processing initiated. '
                      'Note: Full processing logic will be implemented with core face recognition module.'
        }, status=status.HTTP_202_ACCEPTED)


class FaceCropViewSet(viewsets.ModelViewSet):
    """
    ViewSet for FaceCrop model.
    
    Admins: Full CRUD access to all face crops
    Users: Can only update the student field for crops in their own classes
    Read and list access for crops in their own classes
    """
    permission_classes = [IsAuthenticated, IsClassOwnerOrAdmin]
    http_method_names = ['get', 'patch', 'post', 'head', 'options']
    
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
