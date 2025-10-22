from django.urls import path, include


app_name = 'authentication'

urlpatterns = [
    # Djoser endpoints for user management
    path('', include('djoser.urls')),
    # JWT endpoints
    path('', include('djoser.urls.jwt')),
]
