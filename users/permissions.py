from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Только администратор"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


class IsTeacher(permissions.BasePermission):
    """Преподаватель или админ"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['admin', 'teacher']


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Для изменения объекта нужно быть его владельцем или админом.
    Просматривать могут все авторизованные.
    """

    def has_object_permission(self, request, view, obj):
        # Проверка аутентификации
        if not request.user.is_authenticated:
            return False

        # Просмотр разрешён всем авторизованным
        if request.method in permissions.SAFE_METHODS:
            return True

        # Админ может всё
        if request.user.role == 'admin':
            return True

        # Проверка владельца (работает и для Course, и для Lesson)
        if hasattr(obj, 'owner'):
            return obj.owner == request.user

        # Для Lesson проверяем владельца курса
        if hasattr(obj, 'course') and hasattr(obj.course, 'owner'):
            return obj.course.owner == request.user

        return False
