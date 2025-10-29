from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
import csv
import io
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
    original_image_path = serializers.SerializerMethodField()
    processed_image_path = serializers.SerializerMethodField()
    
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
    
    def get_original_image_path(self, obj):
        """Return the URL for the original image."""
        if obj.original_image_path:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.original_image_path.url)
            return obj.original_image_path.url
        return None
    
    def get_processed_image_path(self, obj):
        """Return the URL for the processed image."""
        if obj.processed_image_path:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.processed_image_path.url)
            return obj.processed_image_path.url
        return None
    
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
    embedding = serializers.ListField(child=serializers.FloatField(), read_only=True)
    crop_image_path = serializers.SerializerMethodField()
    
    class Meta:
        model = FaceCrop
        fields = [
            'id', 'image', 'image_id', 'student', 'student_name',
            'crop_image_path', 'coordinates', 'coordinates_dict',
            'confidence_score', 'is_identified', 'embedding_model', 'embedding',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'image', 'image_id', 'crop_image_path', 'coordinates',
            'confidence_score', 'is_identified', 'created_at', 'updated_at',
            'student_name', 'coordinates_dict', 'embedding_model', 'embedding'
        ]
    
    def get_crop_image_path(self, obj):
        """Return the URL for the crop image."""
        if obj.crop_image_path:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.crop_image_path.url)
            return obj.crop_image_path.url
        return None
    
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


class BulkStudentUploadSerializer(serializers.Serializer):
    """
    Serializer for bulk student upload from CSV/Excel files.
    Validates file format and processes student data.
    """
    file = serializers.FileField(required=True)
    has_header = serializers.BooleanField(default=True, required=False)
    
    # File size limit: 5MB
    MAX_FILE_SIZE = 5 * 1024 * 1024
    # Maximum number of students per upload
    MAX_STUDENTS = 1000
    
    ALLOWED_EXTENSIONS = ['csv', 'xlsx', 'xls']
    
    def validate_file(self, value):
        """
        Validate the uploaded file:
        - Check file size
        - Check file extension
        - Validate it's not empty
        """
        # Check file size
        if value.size > self.MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f"File size exceeds maximum allowed size of {self.MAX_FILE_SIZE / (1024 * 1024)}MB"
            )
        
        # Check file extension
        file_extension = value.name.split('.')[-1].lower()
        if file_extension not in self.ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"File extension '.{file_extension}' not allowed. "
                f"Allowed extensions: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )
        
        # Check file is not empty
        if value.size == 0:
            raise serializers.ValidationError("Uploaded file is empty")
        
        return value
    
    def parse_csv_file(self, file_obj, has_header):
        """
        Parse CSV file and extract student data.
        Returns a list of dictionaries with student information.
        """
        students_data = []
        
        try:
            # Read file content
            file_content = file_obj.read().decode('utf-8-sig')  # Handle BOM
            csv_reader = csv.reader(io.StringIO(file_content))
            
            rows = list(csv_reader)
            
            if not rows:
                raise serializers.ValidationError("CSV file contains no data")
            
            # Skip header if present
            start_idx = 1 if has_header else 0
            
            for idx, row in enumerate(rows[start_idx:], start=start_idx + 1):
                # Skip empty rows
                if not row or all(not cell.strip() for cell in row):
                    continue
                
                # Ensure at least 2 columns (first_name, last_name)
                if len(row) < 2:
                    raise serializers.ValidationError(
                        f"Row {idx}: Insufficient columns. Expected at least 2 (first_name, last_name)"
                    )
                
                # Extract student data
                student_data = {
                    'first_name': row[0].strip(),
                    'last_name': row[1].strip(),
                    'student_id': row[2].strip() if len(row) > 2 else '',
                }
                
                # Validate data
                if not student_data['first_name'] or not student_data['last_name']:
                    raise serializers.ValidationError(
                        f"Row {idx}: First name and last name cannot be empty"
                    )
                
                students_data.append(student_data)
            
            if not students_data:
                raise serializers.ValidationError("No valid student data found in file")
            
            if len(students_data) > self.MAX_STUDENTS:
                raise serializers.ValidationError(
                    f"Too many students in file. Maximum allowed: {self.MAX_STUDENTS}"
                )
            
        except UnicodeDecodeError:
            raise serializers.ValidationError(
                "File encoding error. Please ensure the file is UTF-8 encoded"
            )
        except csv.Error as e:
            raise serializers.ValidationError(f"CSV parsing error: {str(e)}")
        
        return students_data
    
    def parse_excel_file(self, file_obj, has_header):
        """
        Parse Excel file and extract student data.
        Returns a list of dictionaries with student information.
        """
        try:
            import openpyxl
        except ImportError:
            raise serializers.ValidationError(
                "Excel support not available. Please install openpyxl"
            )
        
        students_data = []
        
        try:
            workbook = openpyxl.load_workbook(file_obj, read_only=True)
            sheet = workbook.active
            
            rows = list(sheet.iter_rows(values_only=True))
            
            if not rows:
                raise serializers.ValidationError("Excel file contains no data")
            
            # Skip header if present
            start_idx = 1 if has_header else 0
            
            for idx, row in enumerate(rows[start_idx:], start=start_idx + 1):
                # Skip empty rows
                if not row or all(cell is None or str(cell).strip() == '' for cell in row):
                    continue
                
                # Ensure at least 2 columns
                if len(row) < 2:
                    raise serializers.ValidationError(
                        f"Row {idx}: Insufficient columns. Expected at least 2 (first_name, last_name)"
                    )
                
                # Extract student data
                student_data = {
                    'first_name': str(row[0]).strip() if row[0] else '',
                    'last_name': str(row[1]).strip() if row[1] else '',
                    'student_id': str(row[2]).strip() if len(row) > 2 and row[2] else '',
                }
                
                # Validate data
                if not student_data['first_name'] or not student_data['last_name']:
                    raise serializers.ValidationError(
                        f"Row {idx}: First name and last name cannot be empty"
                    )
                
                students_data.append(student_data)
            
            workbook.close()
            
            if not students_data:
                raise serializers.ValidationError("No valid student data found in file")
            
            if len(students_data) > self.MAX_STUDENTS:
                raise serializers.ValidationError(
                    f"Too many students in file. Maximum allowed: {self.MAX_STUDENTS}"
                )
            
        except openpyxl.utils.exceptions.InvalidFileException:
            raise serializers.ValidationError("Invalid Excel file format")
        except Exception as e:
            raise serializers.ValidationError(f"Excel parsing error: {str(e)}")
        
        return students_data
    
    def create_students(self, class_obj, students_data):
        """
        Create students in bulk for the given class.
        Returns statistics about created, skipped, and failed students.
        """
        created_students = []
        skipped_students = []
        
        with transaction.atomic():
            for student_data in students_data:
                # Check if student already exists
                existing = Student.objects.filter(
                    class_enrolled=class_obj,
                    first_name=student_data['first_name'],
                    last_name=student_data['last_name']
                ).first()
                
                if existing:
                    skipped_students.append({
                        'first_name': student_data['first_name'],
                        'last_name': student_data['last_name'],
                        'student_id': student_data['student_id'],
                        'reason': 'Already exists'
                    })
                    continue
                
                # Create new student
                student = Student.objects.create(
                    class_enrolled=class_obj,
                    first_name=student_data['first_name'],
                    last_name=student_data['last_name'],
                    student_id=student_data['student_id']
                )
                created_students.append(student)
        
        return {
            'created': created_students,
            'skipped': skipped_students,
            'total_created': len(created_students),
            'total_skipped': len(skipped_students)
        }


class ProcessImageSerializer(serializers.Serializer):
    """
    Serializer for triggering image processing.
    This endpoint will process an image to extract face crops.
    """
    # Optional parameters for processing configuration
    detector_backend = serializers.ChoiceField(
        choices=['opencv', 'ssd', 'dlib', 'mtcnn', 'retinaface', 'mediapipe', 'yolov8', 'yunet'],
        default='retinaface',
        required=False,
        help_text="Backend to use for face detection"
    )
    confidence_threshold = serializers.FloatField(
        default=0.0,
        min_value=0.0,
        max_value=1.0,
        required=False,
        help_text="Minimum confidence threshold for face detection (0-1)"
    )
    apply_background_effect = serializers.BooleanField(
        default=True,
        required=False,
        help_text="Whether to apply grayscale/shadow to background"
    )
    rectangle_color = serializers.ListField(
        child=serializers.IntegerField(min_value=0, max_value=255),
        default=[0, 255, 0],
        required=False,
        min_length=3,
        max_length=3,
        help_text="BGR color tuple for face rectangles [B, G, R]"
    )
    rectangle_thickness = serializers.IntegerField(
        default=2,
        min_value=1,
        max_value=10,
        required=False,
        help_text="Thickness of rectangle borders in pixels"
    )


class AggregateCropsSerializer(serializers.Serializer):
    """
    Serializer for aggregating face crops from session images into students.
    This endpoint will match unidentified crops to students in the class.
    """
    # Optional parameters for aggregation configuration
    similarity_threshold = serializers.FloatField(
        default=0.7,
        min_value=0.0,
        max_value=1.0,
        required=False,
        help_text="Similarity threshold for matching faces to students"
    )
    auto_assign = serializers.BooleanField(
        default=False,
        required=False,
        help_text="Automatically assign high-confidence matches"
    )


class AggregateClassSerializer(serializers.Serializer):
    """
    Serializer for aggregating attendance across all sessions in a class.
    This endpoint will provide unified class-wide statistics.
    """
    # Optional parameters for class aggregation
    include_unprocessed = serializers.BooleanField(
        default=False,
        required=False,
        help_text="Include unprocessed sessions in aggregation"
    )
    date_from = serializers.DateField(
        required=False,
        help_text="Start date for aggregation (YYYY-MM-DD)"
    )
    date_to = serializers.DateField(
        required=False,
        help_text="End date for aggregation (YYYY-MM-DD)"
    )
    
    def validate(self, data):
        """
        Validate date range if both dates are provided.
        """
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError(
                "date_from must be before or equal to date_to"
            )
        
        return data


class MergeStudentSerializer(serializers.Serializer):
    """
    Serializer for merging two students.
    The source student (the one being merged from) will be deleted after
    all face crops are transferred to the target student.
    """
    target_student_id = serializers.IntegerField(
        required=True,
        help_text="ID of the student to merge into (this student will be kept)"
    )
    
    def validate_target_student_id(self, value):
        """
        Validate that the target student exists.
        """
        if not Student.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                f"Student with ID {value} does not exist"
            )
        return value
    
    def validate(self, data):
        """
        Validate the merge operation.
        Ensures:
        - Source and target are different students
        - Both students belong to the same class
        - User has permission to merge (validated in view)
        """
        # Get source student from context (will be set by the view)
        source_student = self.context.get('source_student')
        if not source_student:
            raise serializers.ValidationError("Source student not provided")
        
        target_student_id = data['target_student_id']
        
        # Check if trying to merge student with itself
        if source_student.id == target_student_id:
            raise serializers.ValidationError(
                "Cannot merge a student with itself"
            )
        
        # Get target student
        try:
            target_student = Student.objects.get(id=target_student_id)
        except Student.DoesNotExist:
            raise serializers.ValidationError(
                f"Target student with ID {target_student_id} does not exist"
            )
        
        # Check if both students belong to the same class
        if source_student.class_enrolled_id != target_student.class_enrolled_id:
            raise serializers.ValidationError(
                "Students must belong to the same class to be merged"
            )
        
        # Add target student to validated data for convenience
        data['target_student'] = target_student
        
        return data


class GenerateEmbeddingSerializer(serializers.Serializer):
    """
    Serializer for generating face embeddings.
    """
    model_name = serializers.ChoiceField(
        choices=['arcface', 'facenet', 'facenet512'],
        default='arcface',
        help_text='Model to use for embedding generation'
    )
    
    def validate_model_name(self, value):
        """Ensure model name is lowercase."""
        return value.lower()


class BulkGenerateEmbeddingsSerializer(serializers.Serializer):
    """
    Serializer for bulk generating embeddings for face crops.
    """
    model_name = serializers.ChoiceField(
        choices=['arcface', 'facenet', 'facenet512'],
        default='arcface',
        help_text='Model to use for embedding generation'
    )
    process_unprocessed_images = serializers.BooleanField(
        default=False,
        help_text='Whether to process unprocessed images before generating embeddings'
    )
    detector_backend = serializers.ChoiceField(
        choices=['opencv', 'ssd', 'dlib', 'mtcnn', 'retinaface', 'mediapipe', 'yolov8', 'yunet'],
        default='retinaface',
        help_text='Detector backend to use for image processing'
    )
    confidence_threshold = serializers.FloatField(
        default=0.5,
        min_value=0.0,
        max_value=1.0,
        help_text='Confidence threshold for face detection'
    )
    apply_background_effect = serializers.BooleanField(
        default=True,
        help_text='Whether to apply background effect to processed images'
    )
    
    def validate_model_name(self, value):
        """Ensure model name is lowercase."""
        return value.lower()


class BulkProcessImagesSerializer(serializers.Serializer):
    """
    Serializer for bulk processing images.
    """
    detector_backend = serializers.ChoiceField(
        choices=['opencv', 'ssd', 'dlib', 'mtcnn', 'retinaface', 'mediapipe', 'yolov8', 'yunet'],
        default='retinaface',
        help_text='Detector backend to use for image processing'
    )
    confidence_threshold = serializers.FloatField(
        default=0.5,
        min_value=0.0,
        max_value=1.0,
        help_text='Confidence threshold for face detection'
    )
    apply_background_effect = serializers.BooleanField(
        default=True,
        help_text='Whether to apply background effect to processed images'
    )
    rectangle_color = serializers.ListField(
        child=serializers.IntegerField(min_value=0, max_value=255),
        min_length=3,
        max_length=3,
        default=[0, 255, 0],
        help_text='RGB color for face rectangles [R, G, B]'
    )
    rectangle_thickness = serializers.IntegerField(
        default=2,
        min_value=1,
        help_text='Thickness of face rectangles'
    )


class ClusterCropsSerializer(serializers.Serializer):
    """
    Serializer for clustering face crops in a session.
    """
    max_clusters = serializers.IntegerField(
        default=10,
        min_value=2,
        max_value=200,
        help_text='Maximum number of clusters to create'
    )
    force_clustering = serializers.BooleanField(
        default=False,
        help_text='If True, force all crops into clusters; if False, allow outliers'
    )
    similarity_threshold = serializers.FloatField(
        default=0.7,
        min_value=0.0,
        max_value=1.0,
        help_text='Minimum similarity for cluster membership (0-1)'
    )


