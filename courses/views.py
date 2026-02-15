from rest_framework.exceptions import NotAuthenticated
from rest_framework.viewsets import ModelViewSet

from rest_framework import serializers, permissions

from courses.models import Course, Lesson
from courses.serializers import CourseSerializer, LessonSerializer


class CourseViewSet(ModelViewSet):
    """ViewSet для выполнения всех CRUD операций с курсами."""

    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]      # IsOwnerOrAdmin

    def perform_create(self, serializer: serializers.Serializer) -> None:
        """Автоматически устанавливает текущего пользователя как владельца создаваемого объекта."""
        if not self.request.user.is_authenticated:
            raise NotAuthenticated('Необходимо авторизоваться для создания курса')
        serializer.save(owner=self.request.user)


# class LessonViewSet(ModelViewSet):
#     queryset = Lesson.objects.all()
#     serializer_class = LessonSerializer
#
#     def get_permissions(self):
#         if self.action in ['create', 'update', 'partial_update', 'destroy']:
#             permission_classes = [IsOwnerOrReadOnly]
#         else:
#             permission_classes = [permissions.IsAuthenticated]
#         return [permission() for permission in permission_classes]
#
#     def perform_create(self, serializer):
#         course = serializer.validated_data['course']
#         if course.owner != self.request.user and self.request.user.role != 'admin':
#             raise permissions.PermissionDenied('Вы не владелец этого курса')
#         serializer.save()

class LessonViewSet(ModelViewSet):
    """ViewSet для выполнения всех CRUD операций с уроками."""
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated]      # IsOwnerOrAdmin

    def perform_create(self, serializer: serializers.Serializer) -> None:
        """Автоматически устанавливает текущего пользователя как владельца создаваемого объекта."""
        if not self.request.user.is_authenticated:
            raise NotAuthenticated('Необходимо авторизоваться для создания курса')
        serializer.save(owner=self.request.user)
