from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admins to access it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin users have full access
        if request.user and request.user.is_staff:
            return True
        
        # Check if the object has an owner attribute
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        
        return False


class IsClassOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission for objects that are related to a class through various relationships.
    Allows access to the class owner or admin users.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin users have full access
        if request.user and request.user.is_staff:
            return True
        
        # Get the class owner based on the object type
        class_owner = self._get_class_owner(obj)
        
        if class_owner:
            return class_owner == request.user
        
        return False
    
    def _get_class_owner(self, obj):
        """
        Determine the class owner based on the object type.
        """
        # Import here to avoid circular imports
        from .models import Class, Student, Session, Image, FaceCrop
        
        if isinstance(obj, Class):
            return obj.owner
        elif isinstance(obj, Student):
            return obj.class_enrolled.owner
        elif isinstance(obj, Session):
            return obj.class_session.owner
        elif isinstance(obj, Image):
            return obj.session.class_session.owner
        elif isinstance(obj, FaceCrop):
            return obj.image.session.class_session.owner
        
        return None


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow read-only access to everyone,
    but only allow write access to admin users.
    """
    
    def has_permission(self, request, view):
        # Read permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to admin users
        return request.user and request.user.is_staff
