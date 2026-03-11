from rest_framework import permissions


class CanCreateTest(permissions.BasePermission):
    """Только преподаватели и админы могут создавать тесты"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ["admin", "teacher"]


class IsTestOwnerOrAdmin(permissions.BasePermission):
    """
    Для изменения/удаления теста нужно быть владельцем или админом.
    Просматривать могут преподаватели (своих уроков) и админы.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Администратор может всё
        if request.user.role == "admin":
            return True

        # Для просмотра (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            # Преподаватели могут просматривать тесты своих уроков
            if request.user.role == "teacher":
                return obj.lesson.owner == request.user or obj.owner == request.user
            return False

        # Для изменения/удаления - только владелец теста
        return obj.owner == request.user


class CanTakeTest(permissions.BasePermission):
    """
    Разрешение на прохождение теста.
    Студенты могут проходить только активные тесты.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Админ и преподаватели не проходят тесты (только просматривают)
        if request.user.role in ["admin", "teacher"]:
            return request.method in permissions.SAFE_METHODS

        # Студенты могут проходить только активные тесты
        if request.user.role == "student":
            if request.method == "POST":
                return obj.is_active
            return True

        return False


class IsAttemptOwner(permissions.BasePermission):
    """
    Разрешение для владельца попытки.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Админ может всё
        if request.user.role == "admin":
            return True

        # Преподаватели могут просматривать попытки студентов своих уроков
        if request.user.role == "teacher":
            if request.method in permissions.SAFE_METHODS:
                return obj.test.lesson.owner == request.user
            return False

        # Студенты - только свои попытки
        return obj.user == request.user
