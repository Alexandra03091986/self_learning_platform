from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from config import settings
from courses.models import Lesson


class Test(models.Model):
    """Модель теста для урока"""
    lesson = models.OneToOneField(
        Lesson,
        on_delete=models.CASCADE,
        related_name="test",
        verbose_name="Урок",
        help_text="Выберите урок для теста"
    )
    title = models.CharField(
        max_length=200,
        verbose_name="Название теста",
        help_text="Введите название теста"
    )
    description = models.TextField(
        verbose_name="Описание теста",
        help_text="Введите описание теста",
        blank=True,
        null=True
    )
    time_limit = models.PositiveIntegerField(
        verbose_name="Лимит времени (минуты)",
        help_text="Укажите время на прохождение теста в минутах",
        default=30,
        validators=[MinValueValidator(1)]
    )
    attempts_allowed = models.PositiveIntegerField(
        verbose_name="Количество попыток",
        help_text="Укажите количество допустимых попыток",
        default=1,
        validators=[MinValueValidator(1)]
    )
    passing_score = models.PositiveIntegerField(
        verbose_name="Проходной балл (%)",
        help_text="Укажите минимальный процент для прохождения",
        default=70,
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    is_active = models.BooleanField(
        verbose_name="Активен",
        help_text="Отметьте, если тест доступен для прохождения",
        default=True
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Владелец",
        help_text="Владелец теста"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )

    def __str__(self):
        return f"Тест: {self.lesson.title} - {self.title}"

    class Meta:
        db_table = "tests"
        verbose_name = "Тест"
        verbose_name_plural = "Тесты"


class Question(models.Model):
    """Модель вопроса в тесте"""
    QUESTION_TYPES = (
        ("single", "Один вариант"),
        ("multiple", "Несколько вариантов"),
        ("text", "Текстовый ответ"),
    )

    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="Тест",
        help_text="Выберите тест"
    )
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPES,
        default='single',
        verbose_name="Тип вопроса",
        help_text="Выберите тип вопроса"
    )
    text = models.TextField(
        verbose_name="Текст вопроса",
        help_text="Введите текст вопроса"
    )
    points = models.PositiveIntegerField(
        verbose_name="Баллы",
        help_text="Количество баллов за правильный ответ",
        default=1,
        validators=[MinValueValidator(1)]
    )
    order = models.PositiveIntegerField(
        verbose_name="Порядок",
        default=0,
        help_text="Порядковый номер вопроса"
    )
    explanation = models.TextField(
        verbose_name="Пояснение",
        help_text="Пояснение к правильному ответу",
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    def __str__(self):
        return self.text[:50]

    class Meta:
        db_table = "questions"
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"


class AnswerOption(models.Model):
    """Модель варианта ответа"""
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="Вопрос"
    )
    text = models.CharField(
        max_length=500,
        verbose_name="Текст ответа",
        help_text="Введите текст ответа"
    )
    is_correct = models.BooleanField(
        verbose_name="Правильный ответ",
        help_text="Отметьте, если это правильный ответ",
        default=False
    )
    order = models.PositiveIntegerField(
        verbose_name="Порядок",
        default=0
    )
    def __str__(self):
        return f"{self.question.text[:30]} - {self.text[:30]}"

    class Meta:
        db_table = "answers"
        verbose_name = "Вариант ответа"
        verbose_name_plural = "Варианты ответов"
        ordering = ['order']


class TestAttempt(models.Model):
    """Модель попытки прохождения теста"""
    STATUS_CHOICES = (
        ('in_progress', 'В процессе'),
        ('completed', 'Завершен'),
        ('timeout', 'Время вышло'),
    )

    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name="Тест"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='test_attempts',
        verbose_name="Пользователь"
    )
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Начало прохождения"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Завершение"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='in_progress',
        verbose_name="Статус"
    )
    score = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Баллы"
    )
    percentage = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Процент выполнения"
    )
    passed = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Тест сдан"
    )

    class Meta:
        verbose_name = "Попытка теста"
        verbose_name_plural = "Попытки тестов"
        ordering = ['-started_at']
        unique_together = ['test', 'user', 'status']  # Только одна активная попытка

    def __str__(self):
        return f"{self.user.username} - {self.test.title} ({self.percentage}%)"


class UserAnswer(models.Model):
    """Модель ответа пользователя на вопрос"""
    attempt = models.ForeignKey(
        TestAttempt,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name="Попытка"
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        verbose_name="Вопрос"
    )
    selected_options = models.ManyToManyField(
        AnswerOption,
        blank=True,
        verbose_name="Выбранные варианты",
        related_name='user_answers'
    )
    text_answer = models.TextField(
        blank=True,
        null=True,
        verbose_name="Текстовый ответ"
    )
    is_correct = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Правильно"
    )
    points_earned = models.FloatField(
        default=0,
        verbose_name="Получено баллов"
    )
    answered_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Время ответа"
    )

    class Meta:
        verbose_name = "Ответ пользователя"
        verbose_name_plural = "Ответы пользователей"
        unique_together = ['attempt', 'question']  # Один ответ на вопрос за попытку

    def __str__(self):
        return f"{self.attempt} - Вопрос {self.question.id}"

class TestResult(models.Model):
    """Результат прохождения теста"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="test_results",
        verbose_name="Студент"
    )
    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name="results",
        verbose_name="Тест"
    )
    attempt = models.OneToOneField(
        TestAttempt,
        on_delete=models.CASCADE,
        related_name="result",
        verbose_name="Попытка",
        null=True,
        blank=True
    )
    score = models.PositiveIntegerField(
        verbose_name="Набрано баллов"
    )
    max_score = models.PositiveIntegerField(
        verbose_name="Максимальный балл"
    )
    percentage = models.FloatField(
        verbose_name="Процент выполнения"
    )
    passed = models.BooleanField(
        verbose_name="Тест сдан"
    )
    completed_at = models.DateTimeField(
        verbose_name="Дата прохождения",
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.test.title} - {self.percentage}%"

    class Meta:
        db_table = "test_results"
        verbose_name = "Результат теста"
        verbose_name_plural = "Результаты тестов"
