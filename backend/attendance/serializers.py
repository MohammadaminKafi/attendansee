from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Class, Student, Session, Image, FaceCrop


User = get_user_model()


class ClassSerializer(serializers.ModelSerializer):
    """
    Serializer for Class model.
    Users can create, read, update, and delete their own classes.
    """
    owner = serializers.ReadOnlyField(source='owner.username')
    owner_id = serializers.ReadOnlyField(source='owner.id')
    student_count = serializers.SerializerMethodField()
    session_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Class
        fields = [
            'id', 'owner', 'owner_id', 'name', 'description', 
            'is_active', 'created_at', 'updated_at',
            'student_count', 'session_count'
        ]
        read_only_fields = ['id', 'owner', 'owner_id', 'created_at', 'updated_at']
    
    def get_student_count(self, obj):
        """Return the number of students in the class."""
        return obj.students.count()
    
    def get_session_count(self, obj):
        """Return the number of sessions in the class."""
        return obj.sessions.count()


class StudentSerializer(serializers.ModelSerializer):
    """
    Serializer for Student model.
    Users can manage students in their own classes.
    """
    full_name = serializers.ReadOnlyField()
    class_name = serializers.ReadOnlyField(source='class_enrolled.name')
    
    class Meta:
        model = Student
        fields = [
            'id', 'class_enrolled', 'class_name', 'first_name', 
            'last_name', 'full_name', 'student_id', 'email', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'full_name', 'class_name']
    
    def validate_class_enrolled(self, value):
        """
        Ensure the user owns the class they're adding a student to.
        """
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if value.owner != request.user:
                raise serializers.ValidationError(
                    "You can only add students to your own classes."
                )
        return value


class SessionSerializer(serializers.ModelSerializer):
    """
    Serializer for Session model.
    Users can manage sessions in their own classes.
    """
    class_name = serializers.ReadOnlyField(source='class_session.name')
    image_count = serializers.SerializerMethodField()
    identified_faces_count = serializers.SerializerMethodField()
    total_faces_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Session
        fields = [
            'id', 'class_session', 'class_name', 'name', 'date', 
            'start_time', 'end_time', 'notes', 'is_processed',
            'created_at', 'updated_at', 'image_count',
            'identified_faces_count', 'total_faces_count'
        ]
        read_only_fields = ['id', 'is_processed', 'created_at', 'updated_at', 'class_name']
    
    def get_image_count(self, obj):
        """Return the number of images in the session."""
        return obj.images.count()
    
    def get_identified_faces_count(self, obj):
        """Return the number of identified face crops in the session."""
        return FaceCrop.objects.filter(
            image__session=obj,
            is_identified=True
        ).count()
    
    def get_total_faces_count(self, obj):
        """Return the total number of face crops in the session."""
        return FaceCrop.objects.filter(image__session=obj).count()
    
    def validate_class_session(self, value):
        """
        Ensure the user owns the class for the session.
        """
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if value.owner != request.user:
                raise serializers.ValidationError(
                    "You can only create sessions for your own classes."
                )
        return value


class ImageSerializer(serializers.ModelSerializer):
    """
    Serializer for Image model.
    Users can upload and manage images in their sessions.
    """
    session_name = serializers.ReadOnlyField(source='session.name')
    class_name = serializers.ReadOnlyField(source='session.class_session.name')
    face_crop_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Image
        fields = [
            'id', 'session', 'session_name', 'class_name',
            'original_image_path', 'processed_image_path',
            'upload_date', 'is_processed', 'processing_date',
            'created_at', 'updated_at', 'face_crop_count'
        ]
        read_only_fields = [
            'id', 'upload_date', 'is_processed', 'processing_date',
            'created_at', 'updated_at', 'session_name', 'class_name'
        ]
    
    def get_face_crop_count(self, obj):
        """Return the number of face crops in the image."""
        return obj.face_crops.count()
    
    def validate_session(self, value):
        """
        Ensure the user owns the class for the session.
        """
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if value.class_session.owner != request.user:
                raise serializers.ValidationError(
                    "You can only upload images to sessions in your own classes."
                )
        return value


class FaceCropSerializer(serializers.ModelSerializer):
    """
    Serializer for FaceCrop model.
    Users can update the student assignment for face crops.
    """
    image_id = serializers.ReadOnlyField(source='image.id')
    student_name = serializers.ReadOnlyField(source='student.full_name')
    coordinates_dict = serializers.SerializerMethodField()
    
    class Meta:
        model = FaceCrop
        fields = [
            'id', 'image', 'image_id', 'student', 'student_name',
            'crop_image_path', 'coordinates', 'coordinates_dict',
            'confidence_score', 'is_identified', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'image', 'image_id', 'crop_image_path', 'coordinates',
            'confidence_score', 'is_identified', 'created_at', 'updated_at',
            'student_name', 'coordinates_dict'
        ]
    
    def get_coordinates_dict(self, obj):
        """Return parsed coordinates as a dictionary."""
        return obj.parse_coordinates()
    
    def validate_student(self, value):
        """
        Ensure the student belongs to the same class as the session.
        Only validate if student is being set (not None).
        """
        if value is None:
            return value
        
        request = self.context.get('request')
        instance = self.instance
        
        if instance:
            # Get the class from the image's session
            session_class = instance.image.session.class_session
            
            # Check if student belongs to the same class
            if value.class_enrolled != session_class:
                raise serializers.ValidationError(
                    "Student must belong to the same class as the session."
                )
            
            # Check if user owns the class
            if request and hasattr(request, 'user'):
                if session_class.owner != request.user:
                    raise serializers.ValidationError(
                        "You can only assign students to face crops in your own classes."
                    )
        
        return value
    
    def update(self, instance, validated_data):
        """
        Update student assignment and automatically set identification status.
        """
        student = validated_data.get('student', instance.student)
        
        if student is not None:
            # Use the model's identify_student method
            confidence = validated_data.get('confidence_score', instance.confidence_score)
            instance.identify_student(student, confidence)
        else:
            # Clear student assignment
            instance.student = None
            instance.is_identified = False
            instance.save()
        
        return instance


class FaceCropDetailSerializer(FaceCropSerializer):
    """
    Detailed serializer for FaceCrop with additional related information.
    """
    session_id = serializers.ReadOnlyField(source='image.session.id')
    session_name = serializers.ReadOnlyField(source='image.session.name')
    class_id = serializers.ReadOnlyField(source='image.session.class_session.id')
    class_name = serializers.ReadOnlyField(source='image.session.class_session.name')
    
    class Meta(FaceCropSerializer.Meta):
        fields = FaceCropSerializer.Meta.fields + [
            'session_id', 'session_name', 'class_id', 'class_name'
        ]
