from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom User model for AttendanSee application.
    
    Two levels of users:
    - Admin: has is_staff=True, can access Django admin
    - Regular User: has is_staff=False, normal user access
    
    Classes and sessions relationships will be handled in the attendance app.
    """
    email = models.EmailField(unique=True)
    
    # Additional fields can be added here as needed
    # e.g., phone_number, profile_picture, etc.
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.username
