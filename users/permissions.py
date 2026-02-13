from rest_framework import permissions, request, views
class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

class IsTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['admin', 'teacher']


class IsOwner(permissions.BasePermission):
    """Проверяет, является ли пользователь владельцем."""

    def has_object_permission(self, request: request.Request, view: views.APIView, obj) -> bool:

        if obj.owner == request.user:
            """Проверяет право доступа к конкретному объекту."""
            return True
        return False
