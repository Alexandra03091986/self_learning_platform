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

# class IsOwnerOrAdmin(permissions.BasePermission):
#     def has_object_permission(self, request, view, obj):
#         # Безопасные методы (GET, HEAD, OPTIONS) — все могут читать
#         if request.method in permissions.SAFE_METHODS:
#             return True
#         # Админ может всё
#         if request.user.role == 'admin':
#             return True
#         # Владелец может редактировать
#         if hasattr(obj, 'owner'):
#             return obj.owner == request.user
#         # Для материалов — проверяем владельца раздела
#         if hasattr(obj, 'section'):
#             return obj.section.owner == request.user
#         return False
