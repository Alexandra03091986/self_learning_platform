from rest_framework.routers import SimpleRouter
from courses.apps import CoursesConfig
from django.urls import path

from courses.views import CourseViewSet

app_name = CoursesConfig.name

router = SimpleRouter()
router.register("", CourseViewSet)

urlpatterns = [
    # path('', )
]

urlpatterns += router.urls