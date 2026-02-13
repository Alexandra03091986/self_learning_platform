from django.db import models

from config import settings


class Course(models.Model):
    """Модель курса"""

    title = models.CharField(
        max_length=100,
        verbose_name="Название курса",
        help_text="Укажите название курса",
    )
    picture = models.ImageField(
        upload_to="courses/picture/",
        verbose_name="Превью курса",
        help_text="Загрузите фото курса",
        blank=True,
        null=True,
    )
    description = models.TextField(
        verbose_name="Описание курса",
        help_text="Укажите описание курса",
        blank=True,
        null=True,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Владелец курса",
        help_text="Укажите владельца курса",
    )
    created_at = models.DateTimeField(
        verbose_name="Дата создания",
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        verbose_name="Дата обновления",
        auto_now=True)

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"

    def __str__(self):
        return self.title


class Lesson(models.Model):
    """Модель урока в рамках курса"""

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="materials",
        verbose_name="Курс",
        help_text="Укажите курс",
    )
    title = models.CharField(
        verbose_name="Название",
        help_text="Укажите название урока",
        max_length=200,
    )
    description = models.TextField(
        verbose_name="Описание урока",
        help_text="Укажите описание урока",
        blank=True,
        null=True,
    )
    picture = models.ImageField(
        upload_to="courses/picture/",
        verbose_name="Превью урока",
        help_text="Загрузите превью урока",
        blank=True,
        null=True,
    )
    video_url = models.URLField(
        verbose_name="Ссылка на видео урока",
        help_text="Введите ссылку на видео урока",
        blank=True,
        null=True,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Владелец",
        help_text="Укажите владельца",
    )
    order = models.PositiveIntegerField(
        verbose_name="Порядок сортировки",
        default=0
    )
    created_at = models.DateTimeField(
        verbose_name="Дата создания",
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        verbose_name="Дата обновления",
        auto_now=True
    )

    def __str__(self):
        return f"{self.course.title} - {self.title}"    # noqa

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
        ordering = ['course', 'order']
