from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentication'
    verbose_name = 'Authentication'
    
    def ready(self):
        """
        Import signals or perform other initialization here if needed.
        """
        pass
