from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import Test, AnswerOption, TestAttempt, UserAnswer, TestResult
from .serializers import (
    TestSerializer, TestListSerializer, TestDetailStudentSerializer,
    TestAttemptSerializer, UserAnswerSerializer,
    TestSubmitSerializer, TestResultSerializer
)
from .permissions import IsTestOwnerOrAdmin, CanTakeTest, IsAttemptOwner, CanCreateTest


class TestViewSet(viewsets.ModelViewSet):
    """ViewSet для управления тестами"""
    queryset = Test.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия и роли"""
        if self.action == 'list':
            return TestListSerializer
        elif self.action == 'retrieve':
            if self.request.user.role == 'student':
                return TestDetailStudentSerializer
        return TestSerializer

    def get_queryset(self):
        """Фильтрация тестов в зависимости от роли"""
        user = self.request.user

        if user.role == 'admin':
            return Test.objects.all()
        elif user.role == 'teacher':
            # Тесты, где преподаватель владелец урока
            tests_from_lessons = Test.objects.filter(lesson__owner=user)
            # Тесты, где преподаватель владелец теста
            tests_owned = Test.objects.filter(owner=user)
            # Объединяем
            return (tests_from_lessons | tests_owned).distinct()
        else:
            # Студенты видят только активные тесты доступных уроков
            return Test.objects.filter(is_active=True)

    def get_permissions(self):
        """Динамическое определение прав"""
        # Для создания теста
        if self.action == 'create':
            self.permission_classes = [permissions.IsAuthenticated, CanCreateTest]
        # Для изменения/удаления используем
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAuthenticated, IsTestOwnerOrAdmin]
        # Права для прохождения теста (специальные действия)
        elif self.action in ['start_attempt', 'submit']:
            self.permission_classes = [permissions.IsAuthenticated, CanTakeTest]
        # Права для просмотра (все остальные действия)
        else:
            self.permission_classes = [permissions.IsAuthenticated]

        # Возвращаем результат с правильными правами
        return super().get_permissions()

    def perform_create(self, serializer):
        """Установка владельца при создании"""
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def start_attempt(self, request, pk=None):
        """
        Начать прохождение теста.
        Создает новую попытку, если нет активной и не превышен лимит.
        """
        test = self.get_object()

        # Проверяем активность теста
        if not test.is_active and request.user.role == 'student':
            raise PermissionDenied("Этот тест недоступен для прохождения")

        # Проверяем количество попыток
        attempts_count = TestAttempt.objects.filter(
            test=test,
            user=request.user
        ).exclude(status='in_progress').count()

        if attempts_count >= test.attempts_allowed:
            raise PermissionDenied(f"Вы исчерпали лимит попыток ({test.attempts_allowed})")

        # Проверяем, нет ли активной попытки
        active_attempt = TestAttempt.objects.filter(
            test=test,
            user=request.user,
            status='in_progress'
        ).first()

        if active_attempt:
            serializer = TestAttemptSerializer(active_attempt)
            return Response({
                'message': 'У вас уже есть активная попытка',
                'attempt': serializer.data
            })

        # Создаем новую попытку
        attempt = TestAttempt.objects.create(
            test=test,
            user=request.user
        )

        serializer = TestAttemptSerializer(attempt)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """
        Отправить все ответы и завершить тест.
        Принимает все ответы сразу.
        """
        test = self.get_object()
        serializer = TestSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 1. СНАЧАЛА проверяем лимит попыток (считаем ВСЕ завершенные)
        completed_count = TestAttempt.objects.filter(
            test=test,
            user=request.user,
            status='completed'
        ).count()

        if completed_count >= test.attempts_allowed:
            # Получаем лучший результат для информативного сообщения
            best_result = TestResult.objects.filter(
                test=test,
                user=request.user,
                status='completed'
            ).order_by('-percentage').first()

            best_percentage = best_result.percentage if best_result else 0

            raise PermissionDenied(
                f"Лимит попыток исчерпан ({test.attempts_allowed}). Лучший результат: {best_percentage}%"
            )

        # 2. Ищем активную попытку
        attempt = TestAttempt.objects.filter(
            test=test,
            user=request.user,
            status='in_progress'
        ).first()

        # 3. Если нет активной, создаем НОВУЮ попытку
        if not attempt:
            attempt = TestAttempt.objects.create(
                test=test,
                user=request.user
            )
            print(f"Создана новая попытка {attempt.id} для пользователя {request.user.id}")

        # 4. Проверка времени
        if test.time_limit:
            minutes_passed = (timezone.now() - attempt.started_at).total_seconds() / 60
            if minutes_passed > test.time_limit:
                attempt.status = 'timeout'
                attempt.save()
                raise ValidationError("Время вышло")

        # 5. Проверяем, не отправлял ли уже ответы на ЭТУ попытку
        if UserAnswer.objects.filter(attempt=attempt).exists():
            raise ValidationError(
                f"Вы уже отправили ответы на попытку #{attempt.id}. "
                f"Для новой попытки вызовите start_attempt"
            )

        # 6. Обработка ответов
        answers_data = serializer.validated_data['answers']
        total_points = 0
        max_points = 0

        for question in test.questions.all():
            max_points += question.points
            user_answer_ids = answers_data.get(str(question.id), [])

            # Создаем ответ для ЭТОЙ попытки
            answer = UserAnswer.objects.create(
                attempt=attempt,
                question=question
            )

            # Добавляем выбранные варианты
            if user_answer_ids:
                options = AnswerOption.objects.filter(id__in=user_answer_ids, question=question)
                answer.selected_options.set(options)

            # Оцениваем ответ
            self._evaluate_answer(answer, question)
            if answer.is_correct:
                total_points += question.points

        # 7. Завершаем тест
        return self._finish_attempt(test, attempt, total_points, max_points)

        # test = self.get_object()
        # serializer = TestSubmitSerializer(data=request.data)
        # serializer.is_valid(raise_exception=True)
        #
        # # Получаем или создаем попытку
        # attempt = TestAttempt.objects.filter(
        #     test=test,
        #     user=request.user,
        #     status='in_progress'
        # ).first()
        #
        # if not attempt:
        #     # Проверка лимита попыток
        #     attempts_count = TestAttempt.objects.filter(
        #         test=test,
        #         user=request.user,
        #         status='completed'
        #     ).count()
        #
        #     if attempts_count >= test.attempts_allowed:
        #         raise PermissionDenied(f"Лимит попыток исчерпан")
        #
        #     attempt = TestAttempt.objects.create(test=test, user=request.user)
        #
        # # Проверка времени
        # if test.time_limit:
        #     minutes_passed = (timezone.now() - attempt.started_at).total_seconds() / 60
        #     if minutes_passed > test.time_limit:
        #         attempt.status = 'timeout'
        #         attempt.save()
        #         raise ValidationError("Время вышло")
        #
        # # Проверяем, не отправлял ли уже ответы
        # if UserAnswer.objects.filter(attempt=attempt).exists():
        #     raise ValidationError("Вы уже отправили ответы на этот тест")
        #
        # # Обработка ответов
        # answers_data = serializer.validated_data['answers']
        # total_points = 0
        # max_points = 0
        #
        # for question in test.questions.all():
        #     max_points += question.points
        #     user_answer_ids = answers_data.get(str(question.id), [])
        #
        #     # Создаем ответ
        #     answer, created = UserAnswer.objects.update_or_create(
        #         attempt=attempt,
        #         question=question,
        #         defaults={}
        #     )
        #
        #     # Очищаем старые выбранные опции
        #     answer.selected_options.clear()
        #
        #     # Добавляем выбранные варианты
        #     if user_answer_ids:
        #         options = AnswerOption.objects.filter(id__in=user_answer_ids, question=question)
        #         answer.selected_options.set(options)
        #
        #     # Оцениваем ответ
        #     self._evaluate_answer(answer, question)
        #     if answer.is_correct:
        #         total_points += question.points
        #
        # # Завершаем тест
        # return self._finish_attempt(test, attempt, total_points, max_points)

    def _evaluate_answer(self, answer, question):
        """Оценка ответа на вопрос"""
        correct_options = set(question.answers.filter(is_correct=True).values_list('id', flat=True))
        selected_options = set(answer.selected_options.values_list('id', flat=True))

        if question.question_type == 'single':
            answer.is_correct = (selected_options == correct_options)
        else:  # multiple
            answer.is_correct = (selected_options == correct_options)

        answer.points_earned = question.points if answer.is_correct else 0
        answer.save()
        # if question.question_type == 'text':
        #     # Текстовые ответы требуют ручной проверки
        #     answer.is_correct = None
        #     answer.points_earned = 0
        # else:
        #     correct_options = set(question.answers.filter(is_correct=True).values_list('id', flat=True))
        #     selected_options = set(answer.selected_options.values_list('id', flat=True))
        #
        #     if question.question_type == 'single':
        #         # answer.is_correct = (selected_options == correct_options and len(selected_options) == 1)
        #         answer.is_correct = (selected_options == correct_options)
        #     else:  # multiple
        #         answer.is_correct = (selected_options == correct_options)
        #
        #     answer.points_earned = question.points if answer.is_correct else 0
        #
        # answer.save()

    def _finish_attempt(self, test, attempt, total_points, max_points):
        """Завершение попытки и сохранение результата"""
        percentage = (total_points / max_points * 100) if max_points > 0 else 0
        passed = percentage >= test.passing_score

        # Обновляем попытку
        attempt.status = 'completed'
        attempt.completed_at = timezone.now()
        attempt.score = total_points
        attempt.percentage = percentage
        attempt.passed = passed
        attempt.save()

        # Создаем результат (НЕ распаковываем!)
        result = TestResult.objects.create(
            attempt=attempt,
            user=attempt.user,
            test=test,
            score=total_points,
            max_score=max_points,
            percentage=percentage,
            passed=passed
        )

        # Проверяем, можно ли создать новую попытку
        completed_count = TestAttempt.objects.filter(
            test=test,
            user=attempt.user,
            status='completed'
        ).count()

        remaining_attempts = test.attempts_allowed - completed_count

        return Response({
            'message': 'Тест успешно завершен',
            'result': TestResultSerializer(result).data,
            'attempts_info': {
                'completed_attempts': completed_count,
                'remaining_attempts': remaining_attempts,
                'total_allowed': test.attempts_allowed
            }
        })


class TestAttemptViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для просмотра попыток прохождения тестов"""
    serializer_class = TestAttemptSerializer
    permission_classes = [permissions.IsAuthenticated, IsAttemptOwner]

    def get_queryset(self):
        user = self.request.user

        if user.role == 'admin':
            return TestAttempt.objects.all()
        elif user.role == 'teacher':
            # Преподаватели видят попытки студентов своих уроков
            return TestAttempt.objects.filter(test__lesson__owner=user)
        else:
            # Студенты видят только свои попытки
            return TestAttempt.objects.filter(user=user)

    @action(detail=True, methods=['get'])
    def get_answers(self, request, pk=None):
        """
        Получить все ответы пользователя на попытку.
        """
        attempt = self.get_object()
        answers = attempt.answers.all()
        serializer = UserAnswerSerializer(answers, many=True)
        return Response(serializer.data)


class TestResultViewSet(viewsets.ReadOnlyModelViewSet):
    """Просмотр результатов"""
    serializer_class = TestResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return TestResult.objects.all()
        elif user.role == 'teacher':
            return TestResult.objects.filter(test__lesson__owner=user)
        else:
            return TestResult.objects.filter(user=user)
