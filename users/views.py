from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from courses.models import Course
from tests.models import TestAttempt
from .models import User
from .paginations import UserPagination
from .permissions import IsAdmin
from .serializers import UserSerializer, UserRegisterSerializer, LoginSerializer


class UserRegisterView(generics.CreateAPIView):
    """
    Регистрация нового пользователя.
    Эндпоинт для создания учётной записи. Доступен всем без аутентификации.
    При успешной регистрации возвращает данные созданного пользователя.
    """

    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(generics.GenericAPIView):
    """
    Аутентификация пользователя и получение JWT токенов.
    Эндпоинт для входа в систему. Возвращает access и refresh токены,
    а также данные пользователя. Access токен используется для доступа к API,
    refresh токен - для обновления access токена.
    """
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data

        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })


class UserListView(generics.ListAPIView):
    """
    Получение списка всех пользователей.
    Доступно ТОЛЬКО администраторам.
    Преподаватели НЕ видят список пользователей (только своих студентов через контекст курсов)
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    pagination_class = UserPagination


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Просмотр, обновление и удаление профиля пользователя.

    Эндпоинт для работы с конкретным пользователем. Права доступа зависят от роли:
    - Администраторы: полный доступ к любому профилю (просмотр, изменение, удаление)
    - Преподаватели: просмотр ТОЛЬКО СВОЕГО профиля (не видят чужие)
    - Студенты: просмотр только своего профиля, без возможности изменения/удаления
    - Анонимные пользователи: доступ запрещён
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        """
        Динамическое определение прав доступа в зависимости от метода запроса.
        """
        # Для изменения/удаления - только админ
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsAdmin()]
        # Для просмотра - все авторизованные (но queryset ограничит)
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        """Для админов используем специальный сериализатор с возможностью менять роль"""
        if self.request.user.is_authenticated and self.request.user.role == 'admin' and self.request.method in ['PUT', 'PATCH']:
            from .serializers import UserAdminSerializer
            return UserAdminSerializer
        return UserSerializer

    def get_queryset(self):
        """Фильтрация queryset в зависимости от роли пользователя.
        Строго по ТЗ:
        - Админ: видит всех
        - Преподаватель: видит ТОЛЬКО себя
        - Студент: видит ТОЛЬКО себя
        """
        # Проверяем, что пользователь аутентифицирован
        if not self.request.user.is_authenticated:
            return User.objects.none()  # Пустой queryset для анонимов

        # Админ видит всех
        if self.request.user.role == 'admin':
            return User.objects.all()

        # Преподаватель и студент видят только себя
        return User.objects.filter(id=self.request.user.id)


class CourseStudentsView(generics.ListAPIView):
    """
    Просмотр студентов, проходящих курс (для преподавателей).
    Преподаватель может видеть только студентов своих курсов.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Только преподаватели и админы
        if user.role not in ['admin', 'teacher']:
            return User.objects.none()

        course_id = self.kwargs.get('course_id')

        try:
            course = Course.objects.get(id=course_id)

            # Проверяем, что преподаватель владеет этим курсом
            if user.role == 'teacher' and course.owner != user:
                return User.objects.none()

            # Находим всех студентов, которые проходили тесты этого курса
            student_ids = TestAttempt.objects.filter(
                test__lesson__course=course
            ).values_list('user_id', flat=True).distinct()

            return User.objects.filter(
                id__in=student_ids,
                role='student'
            )

        except Course.DoesNotExist:
            return User.objects.none()
