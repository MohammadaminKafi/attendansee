from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Enhanced admin interface for User model with comprehensive filtering and search.
    """
    list_display = [
        'username',
        'email',
        'full_name_display',
        'is_staff',
        'is_active',
        'is_superuser',
        'classes_count',
        'date_joined_display',
        'last_login_display'
    ]
    list_filter = [
        'is_staff',
        'is_active',
        'is_superuser',
        'date_joined',
        'last_login',
        ('groups', admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = [
        'username',
        'email',
        'first_name',
        'last_name',
        'classes__name',
    ]
    ordering = ['-date_joined']
    date_hierarchy = 'date_joined'
    
    list_per_page = 50
    show_full_result_count = True
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': (),
            'description': 'Additional user information can be added here.'
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login']
    
    actions = ['activate_users', 'deactivate_users', 'make_staff', 'remove_staff']
    
    def full_name_display(self, obj):
        """Display user's full name."""
        full_name = obj.get_full_name()
        return full_name if full_name else '-'
    full_name_display.short_description = 'Full Name'
    
    def classes_count(self, obj):
        """Display number of classes owned by the user."""
        count = obj.classes.count()
        if count > 0:
            return format_html('<b>{}</b>', count)
        return count
    classes_count.short_description = 'Classes'
    classes_count.admin_order_field = 'classes__count'
    
    def date_joined_display(self, obj):
        """Display formatted date joined."""
        return obj.date_joined.strftime('%Y-%m-%d %H:%M')
    date_joined_display.short_description = 'Date Joined'
    date_joined_display.admin_order_field = 'date_joined'
    
    def last_login_display(self, obj):
        """Display formatted last login."""
        if obj.last_login:
            return obj.last_login.strftime('%Y-%m-%d %H:%M')
        return 'Never'
    last_login_display.short_description = 'Last Login'
    last_login_display.admin_order_field = 'last_login'
    
    # Custom Actions
    def activate_users(self, request, queryset):
        """Activate selected users."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} user(s) activated successfully.')
    activate_users.short_description = 'Activate selected users'
    
    def deactivate_users(self, request, queryset):
        """Deactivate selected users."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} user(s) deactivated successfully.')
    deactivate_users.short_description = 'Deactivate selected users'
    
    def make_staff(self, request, queryset):
        """Make selected users staff members."""
        updated = queryset.update(is_staff=True)
        self.message_user(request, f'{updated} user(s) made staff successfully.')
    make_staff.short_description = 'Make selected users staff'
    
    def remove_staff(self, request, queryset):
        """Remove staff status from selected users."""
        updated = queryset.update(is_staff=False)
        self.message_user(request, f'{updated} user(s) removed from staff successfully.')
    remove_staff.short_description = 'Remove staff status from selected users'
    
    def get_queryset(self, request):
        """Optimize queryset with annotations."""
        qs = super().get_queryset(request)
        qs = qs.prefetch_related('classes')
        return qs
