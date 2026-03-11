from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Кастомная модель пользователя с email для авторизации"""

    ROLE_CHOICES = (
        ("admin", "Администратор"),
        ("teacher", "Преподаватель"),
        ("student", "Студент"),
    )

    role = models.CharField(verbose_name="Роль", max_length=20, choices=ROLE_CHOICES, default="student")
    email = models.EmailField(unique=True, verbose_name="Email", help_text="Укажите почту")
    first_name = models.CharField(
        verbose_name="Имя", max_length=150, blank=False, help_text="Укажите имя"  # Не может быть пустым
    )
    last_name = models.CharField(
        verbose_name="Фамилия", max_length=150, blank=False, help_text="Укажите фамилию"  # Не может быть пустым
    )
    avatar = models.ImageField(
        upload_to="users/avatars",
        null=True,
        blank=True,
        verbose_name="Аватар",
        help_text="Загрузите аватар",
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        verbose_name="О себе",
        help_text="Расскажите о себе",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return f"{self.username} ({self.role})"

    class Meta:
        # db_table = 'users'
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
