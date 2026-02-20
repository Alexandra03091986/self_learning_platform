from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .apps import TestsConfig
from .views import TestViewSet, TestAttemptViewSet, TestResultViewSet

app_name = TestsConfig.name

router = DefaultRouter()
router.register(r'tests', TestViewSet, basename='test')     # Регистрируем ViewSet для тестов
router.register(r'attempts', TestAttemptViewSet, basename='attempt')    # для попыток
router.register(r'results', TestResultViewSet, basename='result')       # для результатов

urlpatterns = [
    path('', include(router.urls)),     # Включаем все URL от роутера
]
