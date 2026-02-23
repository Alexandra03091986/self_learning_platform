from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения данных пользователя."""

    class Meta:
        """Метаданные сериализатора пользователь."""

        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "role", "avatar", "bio")
        read_only_fields = ("id",)


class UserRegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя."""

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
        error_messages={"min_length": "Пароль должен быть не менее 8 символов"},
    )
    password_confirm = serializers.CharField(
        write_only=True, style={"input_type": "password"}, label="Подтверждение пароля"
    )

    class Meta:
        """Метаданные сериализатора."""

        model = User
        fields = ("id", "username", "email", "password", "password_confirm", "first_name", "last_name")
        extra_kwargs = {
            "first_name": {"required": True, "error_messages": {"required": "Имя обязательно для заполнения"}},
            "last_name": {"required": True, "error_messages": {"required": "Фамилия обязательно для заполнения"}},
            "email": {"required": True, "error_messages": {"required": "Email обязателен для заполнения"}},
            "username": {"required": True, "error_messages": {"required": "Имя пользователя обязательно"}},
        }

    def validate_username(self, value):
        """
        Проверка уникальности username.
        """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Пользователь с таким именем уже существует")
        return value

    def validate_email(self, value):
        """
        Проверка уникальности email.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует")
        return value

    def validate(self, data):
        """
        Проверка совпадения паролей.
        """
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError("Пароли не совпадают")
        return data

    def create(self, validated_data):
        """
        Создание нового пользователя.

        Удаляет поле password_confirm из данных и создает пользователя
        с ролью 'student' по умолчанию.
        """
        validated_data.pop("password_confirm")
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """
    Сериализатор для входа пользователя.
    Поддерживает вход по email или username.
    """

    username = serializers.CharField(required=False, help_text="Имя пользователя (если вход по username)")
    email = serializers.EmailField(
        required=False,
        help_text="Email (если вход по email)",
        error_messages={"required": "Email обязателен для входа", "invalid": "Введите корректный email"},
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        error_messages={"required": "Пароль обязателен для входа"},
    )

    def validate(self, data):
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        # Проверяем, что указан хотя бы один идентификатор
        if not username and not email:
            raise serializers.ValidationError("Укажите username или email для входа")

        # Ищем пользователя
        user = None
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise serializers.ValidationError({"username": "Пользователь с таким именем не найден"})
        elif email:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError({"email": "Пользователь с таким email не найден"})

        # Проверяем пароль
        if not user.check_password(password):
            raise serializers.ValidationError({"password": "Неверный пароль"})

        if not user.is_active:
            raise serializers.ValidationError("Учётная запись заблокирована")

        return user

        # if not email:
        #     raise serializers.ValidationError(
        #         {'email': 'Укажите email'}
        #     )
        # Ищем пользователя по email (ОДИН запрос к БД!)
        # try:
        #     user = User.objects.get(email=email)
        # except User.DoesNotExist:
        #     raise serializers.ValidationError(
        #         {'email': 'Пользователь с таким email не найден'}
        #     )
        #
        # # Аутентифицируем по username (т.к. authenticate работает с username)
        # authenticated_user = authenticate(
        #     username=user.username,
        #     password=password
        # )
        #
        # if authenticated_user is None:
        #     raise serializers.ValidationError(
        #         {'password': 'Неверный пароль'}
        #     )
        #
        # if not authenticated_user.is_active:
        #     raise serializers.ValidationError(
        #         {'email': 'Учётная запись заблокирована'}
        #     )
        #
        # return authenticated_user


class UserAdminSerializer(serializers.ModelSerializer):
    """Сериализатор для админов (можно менять роль)"""

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "avatar",
            "bio",
            "is_active",
            "is_staff",
        )
        read_only_fields = ("id",)
