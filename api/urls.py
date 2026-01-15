from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AuthViewSet, LocationViewSet, AnnouncementViewSet, 
    UserProfileViewSet, health_check
)

def health_check(request):
    return JsonResponse({"status": "healthy", "service": "anuniosloc-api"})

router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'locations', LocationViewSet, basename='location')
router.register(r'announcements', AnnouncementViewSet, basename='announcement')
router.register(r'profiles', UserProfileViewSet, basename='profile')

urlpatterns = [
    path('', include(router.urls)),
    path('health/', health_check, name='health_check'),
]