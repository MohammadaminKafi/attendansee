from django.db import models
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.utils import timezone
from pgvector.django import VectorField


class Class(models.Model):
    """
    Represents a class/course taught by a professor.
    Each user (professor) can create multiple classes.
    """
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='classes'
    )
    name = models.CharField(max_length=255, validators=[MinLengthValidator(1)])
    description = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'classes'
        verbose_name = 'Class'
        verbose_name_plural = 'Classes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', '-created_at']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.owner.username})"


class Student(models.Model):
    """
    Represents a student enrolled in a class.
    Students are unique by first_name, last_name, and class combination.
    """
    class_enrolled = models.ForeignKey(
        'Class',
        on_delete=models.CASCADE,
        related_name='students'
    )
    first_name = models.CharField(max_length=150, validators=[MinLengthValidator(1)])
    last_name = models.CharField(max_length=150, validators=[MinLengthValidator(1)])
    student_id = models.CharField(max_length=50, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'students'
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        ordering = ['last_name', 'first_name']
        constraints = [
            models.UniqueConstraint(
                fields=['first_name', 'last_name', 'class_enrolled'],
                name='unique_student_per_class'
            )
        ]
        indexes = [
            models.Index(fields=['class_enrolled', 'last_name', 'first_name']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        """Returns the student's full name."""
        return f"{self.first_name} {self.last_name}"


class Session(models.Model):
    """
    Represents an attendance session for a class.
    Each session can have multiple images taken from different angles.
    """
    class_session = models.ForeignKey(
        'Class',
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    name = models.CharField(max_length=255, validators=[MinLengthValidator(1)])
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    notes = models.TextField(blank=True, default='')
    is_processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sessions'
        verbose_name = 'Session'
        verbose_name_plural = 'Sessions'
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['class_session', '-date']),
            models.Index(fields=['is_processed']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.date}"
    
    def update_processing_status(self):
        """
        Updates the is_processed status based on whether all images
        in the session have been processed.
        """
        total_images = self.images.count()
        if total_images == 0:
            self.is_processed = False
        else:
            processed_images = self.images.filter(is_processed=True).count()
            self.is_processed = (total_images == processed_images)
        self.save(update_fields=['is_processed', 'updated_at'])


class Image(models.Model):
    """
    Represents an image taken during a session.
    Each image can be processed to detect faces.
    """
    session = models.ForeignKey(
        'Session',
        on_delete=models.CASCADE,
        related_name='images'
    )
    original_image_path = models.ImageField(upload_to='session_images/', max_length=500)
    processed_image_path = models.ImageField(upload_to='processed_images/', max_length=500, blank=True, default='')
    upload_date = models.DateTimeField(default=timezone.now)
    is_processed = models.BooleanField(default=False)
    processing_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'images'
        verbose_name = 'Image'
        verbose_name_plural = 'Images'
        ordering = ['-upload_date']
        indexes = [
            models.Index(fields=['session', '-upload_date']),
            models.Index(fields=['is_processed']),
        ]
    
    def __str__(self):
        return f"Image {self.id} - Session {self.session.name}"
    
    def mark_as_processed(self, processed_path):
        """
        Marks the image as processed and updates the processed image path.
        Also updates the parent session's processing status.
        
        Args:
            processed_path: Can be either a file path string or a File object
        """
        self.is_processed = True
        self.processed_image_path = processed_path
        self.processing_date = timezone.now()
        self.save(update_fields=['is_processed', 'processed_image_path', 'processing_date', 'updated_at'])
        
        # Update session processing status
        self.session.update_processing_status()


class FaceCrop(models.Model):
    """
    Represents a face crop detected in an image.
    Can be linked to a student if identified, or remain unidentified.
    """
    # Embedding model choices
    EMBEDDING_MODEL_FACENET = 'facenet'
    EMBEDDING_MODEL_ARCFACE = 'arcface'
    
    EMBEDDING_MODEL_CHOICES = [
        (EMBEDDING_MODEL_FACENET, 'FaceNet (128D)'),
        (EMBEDDING_MODEL_ARCFACE, 'ArcFace (512D)'),
    ]
    
    image = models.ForeignKey(
        'Image',
        on_delete=models.CASCADE,
        related_name='face_crops'
    )
    student = models.ForeignKey(
        'Student',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='face_crops'
    )
    crop_image_path = models.ImageField(upload_to='face_crops/', max_length=500)
    coordinates = models.CharField(
        max_length=255,
        help_text='Face coordinates in format: x,y,width,height'
    )
    confidence_score = models.FloatField(
        null=True,
        blank=True,
        help_text='Confidence score for student identification (0-1)'
    )
    is_identified = models.BooleanField(default=False)
    
    # Embedding fields for similarity search and clustering
    embedding = VectorField(
        dimensions=512,  # Max dimension (ArcFace), FaceNet will use first 128
        null=True,
        blank=True,
        help_text='Face embedding vector for similarity search'
    )
    embedding_model = models.CharField(
        max_length=20,
        choices=EMBEDDING_MODEL_CHOICES,
        null=True,
        blank=True,
        help_text='Model used to generate the embedding'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'face_crops'
        verbose_name = 'Face Crop'
        verbose_name_plural = 'Face Crops'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['image', '-created_at']),
            models.Index(fields=['student']),
            models.Index(fields=['is_identified']),
            models.Index(fields=['embedding_model']),
        ]
    
    def __str__(self):
        if self.student:
            return f"Crop {self.id} - {self.student.full_name}"
        return f"Crop {self.id} - Unidentified"
    
    def identify_student(self, student, confidence=None):
        """
        Links the face crop to a student.
        """
        self.student = student
        self.is_identified = True
        if confidence is not None:
            self.confidence_score = confidence
        self.save(update_fields=['student', 'is_identified', 'confidence_score', 'updated_at'])
    
    def parse_coordinates(self):
        """
        Parses the coordinates string into a dictionary.
        Returns: dict with keys 'x', 'y', 'width', 'height'
        """
        try:
            x, y, width, height = self.coordinates.split(',')
            return {
                'x': int(x.strip()),
                'y': int(y.strip()),
                'width': int(width.strip()),
                'height': int(height.strip())
            }
        except (ValueError, AttributeError):
            return None
    
    @staticmethod
    def format_coordinates(x, y, width, height):
        """
        Formats coordinates into a string for storage.
        """
        return f"{x},{y},{width},{height}"
