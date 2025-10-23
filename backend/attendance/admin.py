from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q, Avg
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Class, Student, Session, Image, FaceCrop


# ============================================================================
# INLINE ADMIN CLASSES
# ============================================================================

class StudentInline(admin.TabularInline):
    """Inline admin for Students in Class."""
    model = Student
    extra = 0
    fields = ('first_name', 'last_name', 'student_id', 'email')
    show_change_link = True


class SessionInline(admin.TabularInline):
    """Inline admin for Sessions in Class."""
    model = Session
    extra = 0
    fields = ('name', 'date', 'start_time', 'end_time', 'is_processed')
    readonly_fields = ('is_processed',)
    show_change_link = True


class ImageInline(admin.TabularInline):
    """Inline admin for Images in Session."""
    model = Image
    extra = 0
    fields = ('original_image_path', 'is_processed', 'upload_date', 'face_crops_count')
    readonly_fields = ('upload_date', 'face_crops_count')
    show_change_link = True
    
    def face_crops_count(self, obj):
        if obj.pk:
            return obj.face_crops.count()
        return 0
    face_crops_count.short_description = 'Face Crops'


class FaceCropInline(admin.TabularInline):
    """Inline admin for FaceCrops in Image."""
    model = FaceCrop
    extra = 0
    fields = ('student', 'is_identified', 'confidence_score', 'coordinates')
    readonly_fields = ('coordinates',)
    show_change_link = True


# ============================================================================
# CUSTOM FILTERS
# ============================================================================

class OwnerFilter(admin.SimpleListFilter):
    """Filter by class owner."""
    title = 'owner'
    parameter_name = 'owner'
    
    def lookups(self, request, model_admin):
        from authentication.models import User
        owners = User.objects.filter(classes__isnull=False).distinct()
        return [(owner.id, f"{owner.username} ({owner.get_full_name()})") for owner in owners]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(owner_id=self.value())
        return queryset


class ClassOwnerFilter(admin.SimpleListFilter):
    """Filter by class owner (for related models)."""
    title = 'class owner'
    parameter_name = 'class_owner'
    
    def lookups(self, request, model_admin):
        from authentication.models import User
        owners = User.objects.filter(classes__isnull=False).distinct()
        return [(owner.id, f"{owner.username}") for owner in owners]
    
    def queryset(self, request, queryset):
        if self.value():
            # This works for Student, Session
            if hasattr(queryset.model, 'class_enrolled'):
                return queryset.filter(class_enrolled__owner_id=self.value())
            elif hasattr(queryset.model, 'class_session'):
                return queryset.filter(class_session__owner_id=self.value())
        return queryset


class ConfidenceScoreFilter(admin.SimpleListFilter):
    """Filter by confidence score ranges."""
    title = 'confidence score'
    parameter_name = 'confidence'
    
    def lookups(self, request, model_admin):
        return [
            ('high', 'High (>= 0.9)'),
            ('medium', 'Medium (0.7 - 0.9)'),
            ('low', 'Low (< 0.7)'),
            ('none', 'No Score'),
        ]
    
    def queryset(self, request, queryset):
        if self.value() == 'high':
            return queryset.filter(confidence_score__gte=0.9)
        elif self.value() == 'medium':
            return queryset.filter(confidence_score__gte=0.7, confidence_score__lt=0.9)
        elif self.value() == 'low':
            return queryset.filter(confidence_score__lt=0.7)
        elif self.value() == 'none':
            return queryset.filter(confidence_score__isnull=True)
        return queryset


class HasEmailFilter(admin.SimpleListFilter):
    """Filter students by whether they have an email."""
    title = 'has email'
    parameter_name = 'has_email'
    
    def lookups(self, request, model_admin):
        return [
            ('yes', 'Yes'),
            ('no', 'No'),
        ]
    
    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.exclude(email='')
        elif self.value() == 'no':
            return queryset.filter(email='')
        return queryset


class HasStudentIDFilter(admin.SimpleListFilter):
    """Filter students by whether they have a student ID."""
    title = 'has student ID'
    parameter_name = 'has_student_id'
    
    def lookups(self, request, model_admin):
        return [
            ('yes', 'Yes'),
            ('no', 'No'),
        ]
    
    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.exclude(student_id='')
        elif self.value() == 'no':
            return queryset.filter(student_id='')
        return queryset


# ============================================================================
# MODEL ADMIN CLASSES
# ============================================================================

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    """Enhanced admin interface for Class model with comprehensive filtering."""
    list_display = [
        'name',
        'owner_display',
        'students_count',
        'sessions_count',
        'is_active_display',
        'created_at_display',
        'updated_at_display'
    ]
    list_filter = [
        'is_active',
        'created_at',
        'updated_at',
        OwnerFilter,
    ]
    search_fields = [
        'name',
        'description',
        'owner__username',
        'owner__email',
        'owner__first_name',
        'owner__last_name',
    ]
    readonly_fields = ['created_at', 'updated_at', 'students_count', 'sessions_count']
    date_hierarchy = 'created_at'
    list_per_page = 50
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('owner', 'name', 'description')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Statistics', {
            'fields': ('students_count', 'sessions_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [StudentInline, SessionInline]
    actions = ['activate_classes', 'deactivate_classes']
    
    def owner_display(self, obj):
        """Display owner with link."""
        url = reverse('admin:authentication_user_change', args=[obj.owner.id])
        return format_html('<a href="{}">{}</a>', url, obj.owner.username)
    owner_display.short_description = 'Owner'
    owner_display.admin_order_field = 'owner__username'
    
    def students_count(self, obj):
        """Display number of students."""
        if hasattr(obj, 'student_count'):
            count = obj.student_count
        else:
            count = obj.students.count()
        if count > 0:
            return format_html('<b>{}</b>', count)
        return count
    students_count.short_description = 'Students'
    
    def sessions_count(self, obj):
        """Display number of sessions."""
        if hasattr(obj, 'session_count'):
            count = obj.session_count
        else:
            count = obj.sessions.count()
        if count > 0:
            return format_html('<b>{}</b>', count)
        return count
    sessions_count.short_description = 'Sessions'
    
    def is_active_display(self, obj):
        """Display active status with icon."""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Active</span>')
        return format_html('<span style="color: red;">✗ Inactive</span>')
    is_active_display.short_description = 'Status'
    is_active_display.admin_order_field = 'is_active'
    
    def created_at_display(self, obj):
        """Display formatted created date."""
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_at_display.short_description = 'Created'
    created_at_display.admin_order_field = 'created_at'
    
    def updated_at_display(self, obj):
        """Display formatted updated date."""
        return obj.updated_at.strftime('%Y-%m-%d %H:%M')
    updated_at_display.short_description = 'Updated'
    updated_at_display.admin_order_field = 'updated_at'
    
    def activate_classes(self, request, queryset):
        """Activate selected classes."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} class(es) activated successfully.')
    activate_classes.short_description = 'Activate selected classes'
    
    def deactivate_classes(self, request, queryset):
        """Deactivate selected classes."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} class(es) deactivated successfully.')
    deactivate_classes.short_description = 'Deactivate selected classes'
    
    def get_queryset(self, request):
        """Optimize queryset with annotations."""
        qs = super().get_queryset(request)
        qs = qs.select_related('owner').annotate(
            student_count=Count('students', distinct=True),
            session_count=Count('sessions', distinct=True)
        )
        return qs


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """Enhanced admin interface for Student model with comprehensive filtering."""
    list_display = [
        'full_name_display',
        'class_link',
        'class_owner_display',
        'student_id_display',
        'email_display',
        'face_crops_count',
        'created_at_display'
    ]
    list_filter = [
        'class_enrolled',
        ClassOwnerFilter,
        'created_at',
        HasEmailFilter,
        HasStudentIDFilter,
    ]
    search_fields = [
        'first_name',
        'last_name',
        'student_id',
        'email',
        'class_enrolled__name',
        'class_enrolled__owner__username',
    ]
    readonly_fields = ['created_at', 'face_crops_count']
    date_hierarchy = 'created_at'
    list_per_page = 100
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('class_enrolled', 'first_name', 'last_name')
        }),
        ('Additional Information', {
            'fields': ('student_id', 'email')
        }),
        ('Statistics', {
            'fields': ('face_crops_count',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['clear_email', 'clear_student_id']
    
    def full_name_display(self, obj):
        """Display full name."""
        return obj.full_name
    full_name_display.short_description = 'Full Name'
    full_name_display.admin_order_field = 'last_name'
    
    def class_link(self, obj):
        """Display class with link."""
        url = reverse('admin:attendance_class_change', args=[obj.class_enrolled.id])
        return format_html('<a href="{}">{}</a>', url, obj.class_enrolled.name)
    class_link.short_description = 'Class'
    class_link.admin_order_field = 'class_enrolled__name'
    
    def class_owner_display(self, obj):
        """Display class owner."""
        return obj.class_enrolled.owner.username
    class_owner_display.short_description = 'Class Owner'
    class_owner_display.admin_order_field = 'class_enrolled__owner__username'
    
    def student_id_display(self, obj):
        """Display student ID or dash."""
        return obj.student_id if obj.student_id else '-'
    student_id_display.short_description = 'Student ID'
    student_id_display.admin_order_field = 'student_id'
    
    def email_display(self, obj):
        """Display email or dash."""
        return obj.email if obj.email else '-'
    email_display.short_description = 'Email'
    email_display.admin_order_field = 'email'
    
    def face_crops_count(self, obj):
        """Display number of face crops."""
        if hasattr(obj, 'crop_count'):
            count = obj.crop_count
        else:
            count = obj.face_crops.count()
        if count > 0:
            return format_html('<b>{}</b>', count)
        return count
    face_crops_count.short_description = 'Face Crops'
    
    def created_at_display(self, obj):
        """Display formatted created date."""
        return obj.created_at.strftime('%Y-%m-%d')
    created_at_display.short_description = 'Created'
    created_at_display.admin_order_field = 'created_at'
    
    def clear_email(self, request, queryset):
        """Clear email for selected students."""
        updated = queryset.update(email='')
        self.message_user(request, f'Email cleared for {updated} student(s).')
    clear_email.short_description = 'Clear email for selected students'
    
    def clear_student_id(self, request, queryset):
        """Clear student ID for selected students."""
        updated = queryset.update(student_id='')
        self.message_user(request, f'Student ID cleared for {updated} student(s).')
    clear_student_id.short_description = 'Clear student ID for selected students'
    
    def get_queryset(self, request):
        """Optimize queryset with annotations."""
        qs = super().get_queryset(request)
        qs = qs.select_related('class_enrolled', 'class_enrolled__owner').annotate(
            crop_count=Count('face_crops', distinct=True)
        )
        return qs


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    """Enhanced admin interface for Session model with comprehensive filtering."""
    list_display = [
        'name',
        'class_link',
        'date_display',
        'time_range_display',
        'is_processed_display',
        'images_count',
        'progress_display',
        'created_at_display'
    ]
    list_filter = [
        'is_processed',
        'date',
        'class_session',
        ClassOwnerFilter,
        'created_at',
    ]
    search_fields = [
        'name',
        'notes',
        'class_session__name',
        'class_session__owner__username',
    ]
    readonly_fields = ['created_at', 'updated_at', 'images_count', 'progress_display']
    date_hierarchy = 'date'
    list_per_page = 50
    
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
        ('Statistics', {
            'fields': ('images_count', 'progress_display'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ImageInline]
    actions = ['mark_as_processed', 'mark_as_unprocessed', 'update_processing_status']
    
    def class_link(self, obj):
        """Display class with link."""
        url = reverse('admin:attendance_class_change', args=[obj.class_session.id])
        return format_html('<a href="{}">{}</a>', url, obj.class_session.name)
    class_link.short_description = 'Class'
    class_link.admin_order_field = 'class_session__name'
    
    def date_display(self, obj):
        """Display formatted date."""
        return obj.date.strftime('%Y-%m-%d')
    date_display.short_description = 'Date'
    date_display.admin_order_field = 'date'
    
    def time_range_display(self, obj):
        """Display time range."""
        if obj.start_time and obj.end_time:
            return f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"
        elif obj.start_time:
            return f"From {obj.start_time.strftime('%H:%M')}"
        elif obj.end_time:
            return f"Until {obj.end_time.strftime('%H:%M')}"
        return '-'
    time_range_display.short_description = 'Time Range'
    
    def is_processed_display(self, obj):
        """Display processing status with icon."""
        if obj.is_processed:
            return format_html('<span style="color: green;">✓ Processed</span>')
        return format_html('<span style="color: orange;">⧗ Pending</span>')
    is_processed_display.short_description = 'Status'
    is_processed_display.admin_order_field = 'is_processed'
    
    def images_count(self, obj):
        """Display number of images."""
        if hasattr(obj, 'image_count'):
            count = obj.image_count
        else:
            count = obj.images.count()
        if count > 0:
            return format_html('<b>{}</b>', count)
        return count
    images_count.short_description = 'Images'
    
    def progress_display(self, obj):
        """Display processing progress."""
        if hasattr(obj, 'image_count') and hasattr(obj, 'processed_image_count'):
            total = obj.image_count
            processed = obj.processed_image_count
        else:
            total = obj.images.count()
            processed = obj.images.filter(is_processed=True).count()
        
        if total == 0:
            return 'No images'
        
        percentage = (processed / total) * 100
        color = 'green' if percentage == 100 else 'orange' if percentage > 0 else 'red'
        return format_html(
            '<span style="color: {};">{}/{} ({:.0f}%)</span>',
            color, processed, total, percentage
        )
    progress_display.short_description = 'Progress'
    
    def created_at_display(self, obj):
        """Display formatted created date."""
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_at_display.short_description = 'Created'
    created_at_display.admin_order_field = 'created_at'
    
    def mark_as_processed(self, request, queryset):
        """Mark selected sessions as processed."""
        updated = queryset.update(is_processed=True)
        self.message_user(request, f'{updated} session(s) marked as processed.')
    mark_as_processed.short_description = 'Mark as processed'
    
    def mark_as_unprocessed(self, request, queryset):
        """Mark selected sessions as unprocessed."""
        updated = queryset.update(is_processed=False)
        self.message_user(request, f'{updated} session(s) marked as unprocessed.')
    mark_as_unprocessed.short_description = 'Mark as unprocessed'
    
    def update_processing_status(self, request, queryset):
        """Update processing status for selected sessions."""
        count = 0
        for session in queryset:
            session.update_processing_status()
            count += 1
        self.message_user(request, f'Processing status updated for {count} session(s).')
    update_processing_status.short_description = 'Update processing status'
    
    def get_queryset(self, request):
        """Optimize queryset with annotations."""
        qs = super().get_queryset(request)
        qs = qs.select_related('class_session', 'class_session__owner').annotate(
            image_count=Count('images', distinct=True),
            processed_image_count=Count('images', filter=Q(images__is_processed=True), distinct=True)
        )
        return qs


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    """Enhanced admin interface for Image model with comprehensive filtering."""
    list_display = [
        'id',
        'session_link',
        'class_display',
        'original_path_display',
        'is_processed_display',
        'face_crops_count',
        'upload_date_display',
        'processing_date_display'
    ]
    list_filter = [
        'is_processed',
        'upload_date',
        'processing_date',
        'session__class_session',
        ClassOwnerFilter,
    ]
    search_fields = [
        'original_image_path',
        'processed_image_path',
        'session__name',
        'session__class_session__name',
    ]
    readonly_fields = [
        'created_at',
        'updated_at',
        'upload_date',
        'processing_date',
        'face_crops_count'
    ]
    date_hierarchy = 'upload_date'
    list_per_page = 50
    
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
        ('Statistics', {
            'fields': ('face_crops_count',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [FaceCropInline]
    actions = ['mark_as_processed', 'mark_as_unprocessed']
    
    def session_link(self, obj):
        """Display session with link."""
        url = reverse('admin:attendance_session_change', args=[obj.session.id])
        return format_html('<a href="{}">{}</a>', url, obj.session.name)
    session_link.short_description = 'Session'
    session_link.admin_order_field = 'session__name'
    
    def class_display(self, obj):
        """Display class name."""
        return obj.session.class_session.name
    class_display.short_description = 'Class'
    class_display.admin_order_field = 'session__class_session__name'
    
    def original_path_display(self, obj):
        """Display truncated original path."""
        path = obj.original_image_path
        if len(path) > 50:
            return f"...{path[-47:]}"
        return path
    original_path_display.short_description = 'Original Path'
    
    def is_processed_display(self, obj):
        """Display processing status with icon."""
        if obj.is_processed:
            return format_html('<span style="color: green;">✓ Processed</span>')
        return format_html('<span style="color: orange;">⧗ Pending</span>')
    is_processed_display.short_description = 'Status'
    is_processed_display.admin_order_field = 'is_processed'
    
    def face_crops_count(self, obj):
        """Display number of face crops."""
        if hasattr(obj, 'crop_count'):
            count = obj.crop_count
        else:
            count = obj.face_crops.count()
        if count > 0:
            return format_html('<b>{}</b>', count)
        return count
    face_crops_count.short_description = 'Face Crops'
    
    def upload_date_display(self, obj):
        """Display formatted upload date."""
        return obj.upload_date.strftime('%Y-%m-%d %H:%M')
    upload_date_display.short_description = 'Uploaded'
    upload_date_display.admin_order_field = 'upload_date'
    
    def processing_date_display(self, obj):
        """Display formatted processing date."""
        if obj.processing_date:
            return obj.processing_date.strftime('%Y-%m-%d %H:%M')
        return '-'
    processing_date_display.short_description = 'Processed'
    processing_date_display.admin_order_field = 'processing_date'
    
    def mark_as_processed(self, request, queryset):
        """Mark selected images as processed."""
        from django.utils import timezone
        updated = queryset.update(is_processed=True, processing_date=timezone.now())
        self.message_user(request, f'{updated} image(s) marked as processed.')
    mark_as_processed.short_description = 'Mark as processed'
    
    def mark_as_unprocessed(self, request, queryset):
        """Mark selected images as unprocessed."""
        updated = queryset.update(is_processed=False, processing_date=None)
        self.message_user(request, f'{updated} image(s) marked as unprocessed.')
    mark_as_unprocessed.short_description = 'Mark as unprocessed'
    
    def get_queryset(self, request):
        """Optimize queryset with annotations."""
        qs = super().get_queryset(request)
        qs = qs.select_related('session', 'session__class_session').annotate(
            crop_count=Count('face_crops', distinct=True)
        )
        return qs


@admin.register(FaceCrop)
class FaceCropAdmin(admin.ModelAdmin):
    """Enhanced admin interface for FaceCrop model with comprehensive filtering."""
    list_display = [
        'id',
        'image_link',
        'session_display',
        'class_display',
        'student_link',
        'is_identified_display',
        'confidence_display',
        'created_at_display'
    ]
    list_filter = [
        'is_identified',
        ConfidenceScoreFilter,
        'created_at',
        'image__session__class_session',
        ClassOwnerFilter,
    ]
    search_fields = [
        'crop_image_path',
        'coordinates',
        'student__first_name',
        'student__last_name',
        'image__session__name',
        'image__session__class_session__name',
    ]
    readonly_fields = [
        'created_at',
        'updated_at',
        'coordinates_display',
        'crop_preview'
    ]
    date_hierarchy = 'created_at'
    list_per_page = 100
    
    fieldsets = (
        ('Image Information', {
            'fields': ('image', 'crop_image_path', 'crop_preview', 'coordinates', 'coordinates_display')
        }),
        ('Identification', {
            'fields': ('student', 'is_identified', 'confidence_score')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_identified', 'mark_as_unidentified', 'clear_student']
    
    def image_link(self, obj):
        """Display image with link."""
        url = reverse('admin:attendance_image_change', args=[obj.image.id])
        return format_html('<a href="{}">Image #{}</a>', url, obj.image.id)
    image_link.short_description = 'Image'
    image_link.admin_order_field = 'image__id'
    
    def session_display(self, obj):
        """Display session name."""
        return obj.image.session.name
    session_display.short_description = 'Session'
    session_display.admin_order_field = 'image__session__name'
    
    def class_display(self, obj):
        """Display class name."""
        return obj.image.session.class_session.name
    class_display.short_description = 'Class'
    class_display.admin_order_field = 'image__session__class_session__name'
    
    def student_link(self, obj):
        """Display student with link."""
        if obj.student:
            url = reverse('admin:attendance_student_change', args=[obj.student.id])
            return format_html('<a href="{}">{}</a>', url, obj.student.full_name)
        return '-'
    student_link.short_description = 'Student'
    student_link.admin_order_field = 'student__last_name'
    
    def is_identified_display(self, obj):
        """Display identification status with icon."""
        if obj.is_identified:
            return format_html('<span style="color: green;">✓ Identified</span>')
        return format_html('<span style="color: gray;">✗ Unidentified</span>')
    is_identified_display.short_description = 'Status'
    is_identified_display.admin_order_field = 'is_identified'
    
    def confidence_display(self, obj):
        """Display confidence score with color coding."""
        if obj.confidence_score is not None:
            score = obj.confidence_score
            if score >= 0.9:
                color = 'green'
            elif score >= 0.7:
                color = 'orange'
            else:
                color = 'red'
            return format_html('<span style="color: {};">{:.2%}</span>', color, score)
        return '-'
    confidence_display.short_description = 'Confidence'
    confidence_display.admin_order_field = 'confidence_score'
    
    def coordinates_display(self, obj):
        """Display parsed coordinates."""
        coords = obj.parse_coordinates()
        if coords:
            return f"x:{coords['x']}, y:{coords['y']}, w:{coords['width']}, h:{coords['height']}"
        return 'Invalid format'
    coordinates_display.short_description = 'Coordinates (Parsed)'
    
    def crop_preview(self, obj):
        """Display image preview if path is accessible."""
        # This would need to be implemented based on your file storage setup
        # For now, just return the path
        return obj.crop_image_path
    crop_preview.short_description = 'Crop Preview'
    
    def created_at_display(self, obj):
        """Display formatted created date."""
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_at_display.short_description = 'Created'
    created_at_display.admin_order_field = 'created_at'
    
    def mark_as_identified(self, request, queryset):
        """Mark selected face crops as identified."""
        updated = queryset.update(is_identified=True)
        self.message_user(request, f'{updated} face crop(s) marked as identified.')
    mark_as_identified.short_description = 'Mark as identified'
    
    def mark_as_unidentified(self, request, queryset):
        """Mark selected face crops as unidentified."""
        updated = queryset.update(is_identified=False, student=None)
        self.message_user(request, f'{updated} face crop(s) marked as unidentified.')
    mark_as_unidentified.short_description = 'Mark as unidentified'
    
    def clear_student(self, request, queryset):
        """Clear student assignment for selected face crops."""
        updated = queryset.update(student=None, is_identified=False)
        self.message_user(request, f'Student cleared for {updated} face crop(s).')
    clear_student.short_description = 'Clear student assignment'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        qs = qs.select_related(
            'image',
            'image__session',
            'image__session__class_session',
            'student',
            'student__class_enrolled'
        )
        return qs

