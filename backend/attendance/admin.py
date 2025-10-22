from django.contrib import admin
from .models import Class, Student, Session, Image, FaceCrop


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    """Admin interface for Class model."""
    list_display = ('name', 'owner', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'owner')
    search_fields = ('name', 'description', 'owner__username', 'owner__email')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('owner', 'name', 'description')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """Admin interface for Student model."""
    list_display = ('full_name', 'class_enrolled', 'student_id', 'email', 'created_at')
    list_filter = ('class_enrolled', 'created_at')
    search_fields = ('first_name', 'last_name', 'student_id', 'email', 'class_enrolled__name')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('class_enrolled', 'first_name', 'last_name')
        }),
        ('Additional Information', {
            'fields': ('student_id', 'email')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    """Admin interface for Session model."""
    list_display = ('name', 'class_session', 'date', 'start_time', 'end_time', 'is_processed', 'created_at')
    list_filter = ('is_processed', 'date', 'class_session', 'created_at')
    search_fields = ('name', 'notes', 'class_session__name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('class_session', 'name', 'date')
        }),
        ('Time', {
            'fields': ('start_time', 'end_time')
        }),
        ('Details', {
            'fields': ('notes', 'is_processed')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    """Admin interface for Image model."""
    list_display = ('id', 'session', 'is_processed', 'upload_date', 'processing_date')
    list_filter = ('is_processed', 'upload_date', 'processing_date', 'session__class_session')
    search_fields = ('original_image_path', 'processed_image_path', 'session__name')
    readonly_fields = ('created_at', 'updated_at', 'upload_date')
    date_hierarchy = 'upload_date'
    
    fieldsets = (
        ('Session', {
            'fields': ('session',)
        }),
        ('Image Paths', {
            'fields': ('original_image_path', 'processed_image_path')
        }),
        ('Processing Status', {
            'fields': ('is_processed', 'upload_date', 'processing_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FaceCrop)
class FaceCropAdmin(admin.ModelAdmin):
    """Admin interface for FaceCrop model."""
    list_display = ('id', 'image', 'student', 'is_identified', 'confidence_score', 'created_at')
    list_filter = ('is_identified', 'created_at', 'student', 'image__session__class_session')
    search_fields = ('crop_image_path', 'coordinates', 'student__first_name', 'student__last_name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Image Information', {
            'fields': ('image', 'crop_image_path', 'coordinates')
        }),
        ('Identification', {
            'fields': ('student', 'is_identified', 'confidence_score')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

