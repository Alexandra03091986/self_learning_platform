from rest_framework.viewsets import ModelViewSet

from rest_framework import serializers

from courses.models import Course
from courses.serializers import CourseSerializer


class CourseViewSet(ModelViewSet):
    """ViewSet для выполнения всех CRUD операций с курсами."""

    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    def perform_create(self, serializer: serializers.Serializer) -> None:
        """Автоматически устанавливает текущего пользователя как владельца создаваемого объекта."""
        serializer.save(owner=self.request.user)



