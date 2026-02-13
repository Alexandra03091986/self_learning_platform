from rest_framework.routers import SimpleRouter
from courses.apps import CoursesConfig
from django.urls import path, include

from courses.views import CourseViewSet, LessonViewSet

app_name = CoursesConfig.name

router = SimpleRouter()
router.register(r'courses', CourseViewSet)
router.register(r'lesson', LessonViewSet)


urlpatterns = [
    path('', include(router.urls)),
]

# urlpatterns += router.urls