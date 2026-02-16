from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .apps import TestsConfig
from .views import TestViewSet, TestAttemptViewSet, TestResultViewSet

app_name = TestsConfig.name

router = DefaultRouter()
router.register(r'tests', TestViewSet, basename='test')
router.register(r'attempts', TestAttemptViewSet, basename='attempt')
router.register(r'results', TestResultViewSet, basename='result')

urlpatterns = [
    path('', include(router.urls)),
]
