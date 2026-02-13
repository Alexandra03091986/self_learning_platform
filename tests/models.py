# from django.db import models
# from courses.models import Lesson
#
#
# class Test(models.Model):
#     material = models.OneToOneField(
#         Material,
#         on_delete=models.CASCADE,
#         related_name='test',
#         verbose_name='Материал'
#     )
#     title = models.CharField('Название теста', max_length=200)
#     description = models.TextField('Описание', blank=True)
#     passing_score = models.PositiveIntegerField('Проходной балл (%)', default=70)
#     time_limit = models.PositiveIntegerField('Лимит времени (минуты)', null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     def __str__(self):
#         return f"Тест: {self.title}"
#
#     class Meta:
#         db_table = 'tests'
#         verbose_name = 'Тест'
#         verbose_name_plural = 'Тесты'
#
#
# class Question(models.Model):
#     QUESTION_TYPES = (
#         ('single', 'Один правильный ответ'),
#         ('multiple', 'Несколько правильных ответов'),
#     )
#
#     test = models.ForeignKey(
#         Test,
#         on_delete=models.CASCADE,
#         related_name='questions',
#         verbose_name='Тест'
#     )
#     text = models.TextField('Текст вопроса')
#     question_type = models.CharField('Тип вопроса', max_length=20, choices=QUESTION_TYPES, default='single')
#     points = models.PositiveIntegerField('Баллы', default=1)
#     order = models.PositiveIntegerField('Порядок', default=0)
#
#     def __str__(self):
#         return self.text[:50]
#
#     class Meta:
#         db_table = 'questions'
#         verbose_name = 'Вопрос'
#         verbose_name_plural = 'Вопросы'
#
#
# class Answer(models.Model):
#     question = models.ForeignKey(
#         Question,
#         on_delete=models.CASCADE,
#         related_name='answers',
#         verbose_name='Вопрос'
#     )
#     text = models.CharField('Текст ответа', max_length=500)
#     is_correct = models.BooleanField('Правильный ответ', default=False)
#
#     def __str__(self):
#         return self.text[:30]
#
#     class Meta:
#         db_table = 'answers'
#         verbose_name = 'Ответ'
#         verbose_name_plural = 'Ответы'
#
#
# class TestResult(models.Model):
#     user = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         related_name='test_results',
#         verbose_name='Студент'
#     )
#     test = models.ForeignKey(
#         Test,
#         on_delete=models.CASCADE,
#         related_name='results',
#         verbose_name='Тест'
#     )
#     score = models.PositiveIntegerField('Набрано баллов')
#     max_score = models.PositiveIntegerField('Максимальный балл')
#     percentage = models.FloatField('Процент выполнения')
#     passed = models.BooleanField('Тест сдан')
#     completed_at = models.DateTimeField('Дата прохождения', auto_now_add=True)
#
#     def __str__(self):
#         return f"{self.user.username} - {self.test.title} - {self.percentage}%"
#
#     class Meta:
#         db_table = 'test_results'
#         verbose_name = 'Результат теста'
#         verbose_name_plural = 'Результаты тестов'
#
#
# class UserAnswer(models.Model):
#     result = models.ForeignKey(TestResult, on_delete=models.CASCADE, related_name='answers')
#     question = models.ForeignKey(Question, on_delete=models.CASCADE)
#     selected_answers = models.ManyToManyField(Answer)  # какие ответы выбрал
#     is_correct = models.BooleanField(default=False)
#     points_earned = models.PositiveIntegerField(default=0)
#