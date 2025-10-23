from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClassViewSet, StudentViewSet, SessionViewSet,
    ImageViewSet, FaceCropViewSet
)


app_name = 'attendance'

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'classes', ClassViewSet, basename='class')
router.register(r'students', StudentViewSet, basename='student')
router.register(r'sessions', SessionViewSet, basename='session')
router.register(r'images', ImageViewSet, basename='image')
router.register(r'face-crops', FaceCropViewSet, basename='facecrop')

urlpatterns = [
    path('', include(router.urls)),
]
