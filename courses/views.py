from rest_framework.exceptions import NotAuthenticated
from rest_framework.viewsets import ModelViewSet

from rest_framework import serializers, permissions

from courses.models import Course, Lesson
from courses.serializers import CourseSerializer, LessonSerializer
from users.permissions import IsTeacher, IsOwnerOrAdmin


class CourseViewSet(ModelViewSet):
    """ViewSet для выполнения всех CRUD операций с курсами."""

    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    def get_permissions(self):
        """
        Права доступа:
        - Создание: только преподаватели и админы
        - Изменение/удаление: владелец или админ
        - Просмотр: все авторизованные
        """
        if self.action == 'create':
            # Только преподаватели и админы могут создавать
            return [IsTeacher()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Для изменения/удаления проверяем владельца или админа
            return [IsOwnerOrAdmin()]
        else:
            # Просмотр - все авторизованные
            return [permissions.IsAuthenticated()]

    def perform_create(self, serializer: serializers.Serializer) -> None:
        """Автоматически устанавливает текущего пользователя как владельца создаваемого объекта."""
        if not self.request.user.is_authenticated:
            raise NotAuthenticated('Необходимо авторизоваться для создания курса')
        serializer.save(owner=self.request.user)


class LessonViewSet(ModelViewSet):
    """ViewSet для выполнения всех CRUD операций с уроками."""
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def get_permissions(self):
        """
        Права доступа:
        - Создание: только преподаватели и админы
        - Изменение/удаление: владелец или админ
        - Просмотр: все авторизованные
        """
        if self.action == 'create':
            return [IsTeacher()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwnerOrAdmin()]
        else:
            return [permissions.IsAuthenticated()]

    def perform_create(self, serializer: serializers.Serializer) -> None:
        """Автоматически устанавливает текущего пользователя как владельца создаваемого объекта."""

        # Проверка аутентификации
        if not self.request.user.is_authenticated:
            raise NotAuthenticated('Необходимо авторизоваться для создания урока')

        # Получаем курс из данных
        course = serializer.validated_data['course']

        # Разрешаем админу или владельцу курса
        if not (self.request.user.role == 'admin' or course.owner == self.request.user):
            raise permissions.PermissionDenied('Можно создавать уроки только в своих курсах')
        # Сохраняем с владельцем
        serializer.save(owner=self.request.user)
