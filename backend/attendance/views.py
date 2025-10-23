from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from .models import Class, Student, Session, Image, FaceCrop
from .serializers import (
    ClassSerializer, StudentSerializer, SessionSerializer,
    ImageSerializer, FaceCropSerializer, FaceCropDetailSerializer
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
