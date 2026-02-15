from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
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
    Возвращает список всех зарегистрированных пользователей.
    Доступно только администраторам.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Просмотр, обновление и удаление профиля пользователя.

    Эндпоинт для работы с конкретным пользователем. Права доступа зависят от роли:
    - Администраторы: полный доступ к любому профилю (просмотр, изменение, удаление)
    - Преподаватели: просмотр любого профиля, но без возможности изменения/удаления
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

    def get_queryset(self):
        """Фильтрация queryset в зависимости от роли пользователя"""
        # Проверяем, что пользователь аутентифицирован
        if not self.request.user.is_authenticated:
            return User.objects.none()  # Пустой queryset для анонимов
        # Администраторы и преподаватели видят всех пользователей
        if self.request.user.role in ['admin', 'teacher']:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)     # Студент - только себя
