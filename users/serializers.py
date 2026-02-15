from rest_framework import serializers
from django.contrib.auth import authenticate

from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения данных пользователя."""

    class Meta:
        """Метаданные сериализатора пользователь."""
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'avatar', 'bio')
        read_only_fields = ('id',)

class UserRegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя."""

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
        error_messages={
            'min_length': 'Пароль должен быть не менее 8 символов'
        }
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        label='Подтверждение пароля'
    )

    class Meta:
        """Метаданные сериализатора."""
        model = User
        fields = ('id', 'username', 'email', 'password', 'password_confirm', 'first_name', 'last_name', 'role')
        extra_kwargs = {
            'first_name': {
                'required': True,
                'error_messages': {'required': 'Имя обязательно для заполнения'}
            },
            'last_name': {
                'required': True,
                'error_messages': {'required': 'Фамилия обязательно для заполнения'}
            },
            'email': {
                'required': True,
                'error_messages': {'required': 'Email обязателен для заполнения'}
            },
            'username': {
                'required': True,
                'error_messages': {'required': 'Имя пользователя обязательно'}
            },
            'role': {
                'required': True,
                'error_messages': {
                    'required': 'Пожалуйста, выберите роль (teacher или student)'
                }
            }
        }

    def validate_role(self, value):
        """
        Проверка выбранной роли.
        Запрещаем регистрацию как администратор.
        """
        if value == 'admin':
            raise serializers.ValidationError(
                'Невозможно зарегистрироваться как администратор'
            )
        if value not in ['teacher', 'student']:
            raise serializers.ValidationError(
                'Роль должна быть "teacher" (преподаватель) или "student" (студент)'
            )
        return value

    def validate_username(self, value):
        """
        Проверка уникальности username.
        """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                'Пользователь с таким именем уже существует'
            )
        return value

    def validate_email(self, value):
        """
        Проверка уникальности email.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'Пользователь с таким email уже существует'
            )
        return value

    def validate(self, data):
        """
        Проверка совпадения паролей.
        """
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError('Пароли не совпадают')
        return data

    def create(self, validated_data):
        """
        Создание пользователя с указанной ролью.
        """
        validated_data.pop('password_confirm')
        # Создаём пользователя через create_user (хэширует пароль)
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """
    Сериализатор для входа пользователя по email.
    """
    email = serializers.EmailField(
        required=True,
        error_messages={
            'required': 'Email обязателен для входа',
            'invalid': 'Введите корректный email'
        }
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        error_messages={
            'required': 'Пароль обязателен для входа'
        }
    )

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if not email:
            raise serializers.ValidationError(
                {'email': 'Укажите email'}
            )

        # Ищем пользователя по email (ОДИН запрос к БД!)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {'email': 'Пользователь с таким email не найден'}
            )

        # Аутентифицируем по username (т.к. authenticate работает с username)
        authenticated_user = authenticate(
            username=user.username,
            password=password
        )

        if not authenticated_user:
            raise serializers.ValidationError(
                {'password': 'Неверный пароль'}
            )

        if not authenticated_user.is_active:
            raise serializers.ValidationError(
                {'email': 'Учётная запись заблокирована'}
            )

        return authenticated_user

# class LoginSerializer(serializers.Serializer):
#     """
#     Сериализатор для входа пользователя.
#     """
#     username = serializers.CharField(required=False)
#     email = serializers.EmailField(required=False)
#     password = serializers.CharField(write_only=True)
#
#     def validate(self, data):
#         # Поддержка входа по username или email
#         username = data.get('username')
#         email = data.get('email')
#         password = data.get('password')
#
#         if not username and not email:
#             raise serializers.ValidationError('Укажите username или email')
#
#         # Аутентификация по username
#         user = None
#         if username:
#             user = authenticate(username=username, password=password)
#
#         # Если не получилось, пробуем найти пользователя по email
#         if not user and email:
#             try:
#                 user_obj = User.objects.get(email=email)
#                 user = authenticate(username=user_obj.username, password=password)
#             except User.DoesNotExist:
#                 pass
#
#         if user and user.is_active:
#             return user
#         raise serializers.ValidationError('Неверный логин или пароль')
