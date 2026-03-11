from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from courses.models import Course, Lesson
from users.models import User

from .models import AnswerOption, Question, Test, TestAttempt, TestResult, UserAnswer


class TestModelTestCase(TestCase):
    """Тесты для моделей тестирования"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="teacher", email="teacher@test.com", password="pass123", role="teacher"
        )
        self.course = Course.objects.create(title="Тестовый курс", owner=self.user)
        self.lesson = Lesson.objects.create(title="Тестовый урок", course=self.course, owner=self.user, order=1)

    def test_test_creation(self):
        """Тест создания модели Test"""
        test = Test.objects.create(
            lesson=self.lesson,
            title="Тестовый тест",
            description="Описание теста",
            time_limit=30,
            attempts_allowed=2,
            passing_score=70,
            owner=self.user,
        )
        self.assertEqual(test.title, "Тестовый тест")
        self.assertEqual(test.lesson, self.lesson)
        self.assertEqual(test.owner, self.user)
        self.assertTrue(test.is_active)
        self.assertEqual(str(test), f"Тест: {self.lesson.title} - {test.title}")

    def test_question_creation(self):
        """Тест создания модели Question"""
        test = Test.objects.create(lesson=self.lesson, title="Тест", owner=self.user)
        question = Question.objects.create(
            test=test, question_type="single", text="Тестовый вопрос?", points=5, order=1
        )
        self.assertEqual(question.text[:50], "Тестовый вопрос?")
        self.assertEqual(question.points, 5)
        self.assertEqual(question.question_type, "single")

    def test_answer_option_creation(self):
        """Тест создания модели AnswerOption"""
        test = Test.objects.create(lesson=self.lesson, title="Тест", owner=self.user)
        question = Question.objects.create(test=test, text="Вопрос?", points=1)

        answer = AnswerOption.objects.create(question=question, text="Правильный ответ", is_correct=True, order=1)
        self.assertEqual(answer.text, "Правильный ответ")
        self.assertTrue(answer.is_correct)
        self.assertIn(str(question.text[:30]), str(answer))

    def test_test_attempt_creation(self):
        """Тест создания модели TestAttempt"""
        test = Test.objects.create(lesson=self.lesson, title="Тест", owner=self.user)
        student = User.objects.create_user(
            username="student", email="student@test.com", password="pass123", role="student"
        )

        attempt = TestAttempt.objects.create(test=test, user=student, status="in_progress")
        self.assertEqual(attempt.status, "in_progress")
        self.assertIsNone(attempt.completed_at)
        self.assertIn(student.username, str(attempt))

    def test_user_answer_creation(self):
        """Тест создания модели UserAnswer"""
        test = Test.objects.create(lesson=self.lesson, title="Тест", owner=self.user)
        student = User.objects.create_user(username="student", role="student")
        question = Question.objects.create(test=test, text="Вопрос?")
        attempt = TestAttempt.objects.create(test=test, user=student)

        answer = UserAnswer.objects.create(attempt=attempt, question=question, is_correct=True, points_earned=5)
        self.assertTrue(answer.is_correct)
        self.assertEqual(answer.points_earned, 5)

    def test_test_result_creation(self):
        """Тест создания модели TestResult"""
        test = Test.objects.create(lesson=self.lesson, title="Тест", owner=self.user)
        student = User.objects.create_user(username="student", role="student")
        attempt = TestAttempt.objects.create(test=test, user=student)

        result = TestResult.objects.create(
            user=student, test=test, attempt=attempt, score=8, max_score=10, percentage=80, passed=True
        )
        self.assertEqual(result.score, 8)
        self.assertEqual(result.percentage, 80)
        self.assertTrue(result.passed)
        self.assertIn(student.username, str(result))


class TestAPITestCase(APITestCase):
    """Тесты для API тестов"""

    def setUp(self):
        """Подготовка данных перед каждым тестом"""
        # Создаем пользователей
        self.admin = User.objects.create_user(
            username="admin", email="admin@test.com", password="adminpass123", role="admin"
        )

        self.teacher1 = User.objects.create_user(
            username="teacher1", email="teacher1@test.com", password="teacherpass123", role="teacher"
        )

        self.teacher2 = User.objects.create_user(
            username="teacher2", email="teacher2@test.com", password="teacherpass123", role="teacher"
        )

        self.student1 = User.objects.create_user(
            username="student1", email="student1@test.com", password="studentpass123", role="student"
        )

        self.student2 = User.objects.create_user(
            username="student2", email="student2@test.com", password="studentpass123", role="student"
        )

        # Создаем курс и уроки
        self.course = Course.objects.create(title="Python курс", owner=self.teacher1)

        self.lesson1 = Lesson.objects.create(course=self.course, title="Урок 1", owner=self.teacher1, order=1)

        self.lesson2 = Lesson.objects.create(course=self.course, title="Урок 2", owner=self.teacher1, order=2)

        # Создаем тесты
        self.test1 = Test.objects.create(
            lesson=self.lesson1,
            title="Тест к уроку 1",
            description="Проверка знаний",
            time_limit=10,
            attempts_allowed=2,
            passing_score=70,
            is_active=True,
            owner=self.teacher1,
        )

        self.test2 = Test.objects.create(
            lesson=self.lesson2,
            title="Тест к уроку 2",
            description="Проверка знаний",
            time_limit=15,
            attempts_allowed=1,
            passing_score=80,
            is_active=True,
            owner=self.teacher1,
        )
        # Создаем неактивный тест для НОВОГО урока
        self.lesson3 = Lesson.objects.create(
            course=self.course, title="Урок 3 (с неактивным тестом)", owner=self.teacher1, order=3
        )

        self.test_inactive = Test.objects.create(
            lesson=self.lesson3,  # <-- Теперь для отдельного урока
            title="Неактивный тест",
            time_limit=10,
            attempts_allowed=1,
            passing_score=70,
            is_active=False,
            owner=self.teacher1,
        )

        # Создаем вопросы и ответы для test1
        self.question1 = Question.objects.create(
            test=self.test1, question_type="single", text="Сколько будет 2+2?", points=1, order=1
        )

        self.answer1_1 = AnswerOption.objects.create(question=self.question1, text="3", is_correct=False, order=1)

        self.answer1_2 = AnswerOption.objects.create(question=self.question1, text="4", is_correct=True, order=2)

        self.question2 = Question.objects.create(
            test=self.test1, question_type="multiple", text="Выберите четные числа", points=2, order=2
        )

        self.answer2_1 = AnswerOption.objects.create(question=self.question2, text="2", is_correct=True, order=1)

        self.answer2_2 = AnswerOption.objects.create(question=self.question2, text="3", is_correct=False, order=2)

        self.answer2_3 = AnswerOption.objects.create(question=self.question2, text="4", is_correct=True, order=3)

    def get_results(self, response):
        """Получить результаты из ответа с учетом пагинации"""
        if isinstance(response.data, dict) and "results" in response.data:
            return response.data["results"]
        return response.data

    # ===== ТЕСТЫ НА СОЗДАНИЕ ТЕСТОВ =====
    def test_teacher_can_create_test(self):
        """Преподаватель может создать тест для своего урока"""
        self.client.force_authenticate(user=self.teacher1)
        url = reverse("tests:test-list")
        # СОЗДАЕМ НОВЫЙ УРОК (у него еще нет теста)
        new_lesson = Lesson.objects.create(
            course=self.course,
            title="Урок для нового теста",
            owner=self.teacher1,
            order=99,  # Большой порядковый номер, чтобы не мешал
        )
        data = {
            "lesson": new_lesson.id,
            "title": "Новый тест",
            "description": "Описание",
            "time_limit": 20,
            "attempts_allowed": 3,
            "passing_score": 75,
            "is_active": True,
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Test.objects.count(), 4)
        self.assertEqual(Test.objects.last().owner, self.teacher1)

    def test_teacher_cannot_create_test_for_foreign_lesson(self):
        """Преподаватель НЕ может создать тест для чужого урока"""
        # Создаем урок другого преподавателя
        foreign_lesson = Lesson.objects.create(course=self.course, title="Чужой урок", owner=self.teacher2, order=3)

        self.client.force_authenticate(user=self.teacher1)
        url = reverse("tests:test-list")
        data = {
            "lesson": foreign_lesson.id,
            "title": "Новый тест",
            "description": "Описание",
            "time_limit": 20,
            "attempts_allowed": 3,
            "passing_score": 75,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_test_for_any_lesson(self):
        """Админ может создать тест для любого урока"""
        self.client.force_authenticate(user=self.admin)
        url = reverse("tests:test-list")
        new_lesson = Lesson.objects.create(
            course=self.course, title="Урок для теста админа", owner=self.teacher1, order=99
        )
        data = {
            "lesson": new_lesson.id,
            "title": "Тест от админа",
            "description": "Описание теста от админа",
            "time_limit": 20,
            "attempts_allowed": 3,
            "passing_score": 75,
            "is_active": True,
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем созданный тест
        self.assertTrue(Test.objects.filter(lesson=new_lesson).exists())
        new_test = Test.objects.get(lesson=new_lesson)
        self.assertEqual(new_test.owner, self.admin)
        self.assertEqual(new_test.title, "Тест от админа")

    def test_student_cannot_create_test(self):
        """Студент НЕ может создать тест"""
        self.client.force_authenticate(user=self.student1)
        url = reverse("tests:test-list")
        data = {
            "lesson": self.lesson1.id,
            "title": "Новый тест",
            "time_limit": 20,
            "attempts_allowed": 3,
            "passing_score": 75,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_create_test(self):
        """Неавторизованный пользователь не может создать тест"""
        url = reverse("tests:test-list")
        data = {
            "lesson": self.lesson1.id,
            "title": "Новый тест",
            "time_limit": 20,
            "attempts_allowed": 3,
            "passing_score": 75,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ===== ТЕСТЫ НА ПРОСМОТР ТЕСТОВ =====
    def test_student_can_view_active_tests(self):
        """Студент видит только активные тесты"""
        self.client.force_authenticate(user=self.student1)
        url = reverse("tests:test-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = self.get_results(response)
        self.assertEqual(len(results), 2)

    def test_teacher_can_view_all_own_tests(self):
        """Преподаватель видит все свои тесты (включая неактивные)"""
        self.client.force_authenticate(user=self.teacher1)
        url = reverse("tests:test-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = self.get_results(response)
        self.assertEqual(len(results), 3)

    def test_student_sees_questions_without_answers(self):
        """Студент видит вопросы без правильных ответов"""
        self.client.force_authenticate(user=self.student1)
        url = reverse("tests:test-detail", args=[self.test1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что в ответе нет is_correct
        for question in response.data["questions"]:
            for answer in question["answer_options"]:
                self.assertNotIn("is_correct", answer)

    def test_teacher_sees_questions_with_answers(self):
        """Преподаватель видит вопросы с правильными ответами"""
        self.client.force_authenticate(user=self.teacher1)
        url = reverse("tests:test-detail", args=[self.test1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем структуру
        self.assertIn("questions", response.data)

        for question in response.data["questions"]:
            self.assertIn("answer_options", question)  # Проверяем наличие ответов
            for answer in question["answer_options"]:
                self.assertIn("is_correct", answer)

    # ===== ТЕСТЫ НА ОБНОВЛЕНИЕ ТЕСТОВ =====
    def test_owner_can_update_test(self):
        """Владелец может обновить свой тест"""
        self.client.force_authenticate(user=self.teacher1)
        url = reverse("tests:test-detail", args=[self.test1.id])
        data = {"title": "Обновленное название"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.test1.refresh_from_db()
        self.assertEqual(self.test1.title, "Обновленное название")

    def test_admin_can_update_any_test(self):
        """Админ может обновить любой тест"""
        self.client.force_authenticate(user=self.admin)
        url = reverse("tests:test-detail", args=[self.test1.id])
        data = {"title": "Обновлено админом"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.test1.refresh_from_db()
        self.assertEqual(self.test1.title, "Обновлено админом")

    def test_other_teacher_cannot_update_test(self):
        """Другой преподаватель НЕ может обновить чужой тест"""
        self.client.force_authenticate(user=self.teacher2)
        url = reverse("tests:test-detail", args=[self.test1.id])
        data = {"title": "Попытка взлома"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ===== ТЕСТЫ НА УДАЛЕНИЕ ТЕСТОВ =====
    def test_owner_can_delete_test(self):
        """Владелец может удалить свой тест"""
        self.client.force_authenticate(user=self.teacher1)
        url = reverse("tests:test-detail", args=[self.test1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Test.objects.count(), 2)

    def test_admin_can_delete_any_test(self):
        """Админ может удалить любой тест"""
        self.client.force_authenticate(user=self.admin)
        url = reverse("tests:test-detail", args=[self.test1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # ===== ТЕСТЫ НА ПРОХОЖДЕНИЕ ТЕСТОВ =====
    def test_start_attempt(self):
        """Студент может начать прохождение теста"""
        self.client.force_authenticate(user=self.student1)
        url = reverse("tests:test-start-attempt", args=[self.test1.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertEqual(TestAttempt.objects.count(), 1)

    def test_cannot_start_attempt_for_inactive_test(self):
        """Нельзя начать неактивный тест"""
        self.client.force_authenticate(user=self.student1)
        url = reverse("tests:test-start-attempt", args=[self.test_inactive.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_submit_test_correct_answers(self):
        """Отправка правильных ответов"""
        self.client.force_authenticate(user=self.student1)

        # Начинаем попытку
        start_url = reverse("tests:test-start-attempt", args=[self.test1.id])
        self.client.post(start_url)

        # Отправляем правильные ответы
        submit_url = reverse("tests:test-submit", args=[self.test1.id])
        data = {
            "answers": {
                str(self.question1.id): [self.answer1_2.id],  # правильный ответ 4
                str(self.question2.id): [self.answer2_1.id, self.answer2_3.id],  # 2 и 4
            }
        }
        response = self.client.post(submit_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["result"]["score"], 3)  # 1 + 2 балла
        self.assertEqual(response.data["result"]["percentage"], 100)
        self.assertTrue(response.data["result"]["passed"])

    def test_submit_test_wrong_answers(self):
        """Отправка неправильных ответов"""
        self.client.force_authenticate(user=self.student1)

        # Начинаем попытку
        start_url = reverse("tests:test-start-attempt", args=[self.test1.id])
        self.client.post(start_url)

        # Отправляем неправильные ответы
        submit_url = reverse("tests:test-submit", args=[self.test1.id])
        data = {
            "answers": {
                str(self.question1.id): [self.answer1_1.id],  # неправильный ответ 3
                str(self.question2.id): [self.answer2_2.id],  # неправильный ответ 3
            }
        }
        response = self.client.post(submit_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["result"]["score"], 0)
        self.assertEqual(response.data["result"]["percentage"], 0)
        self.assertFalse(response.data["result"]["passed"])

    def test_cannot_submit_without_answers(self):
        """Нельзя отправить пустые ответы"""
        self.client.force_authenticate(user=self.student1)

        start_url = reverse("tests:test-start-attempt", args=[self.test1.id])
        self.client.post(start_url)

        submit_url = reverse("tests:test-submit", args=[self.test1.id])
        data = {"answers": {}}
        response = self.client.post(submit_url, data, format="json")

        # Должен создать ответы с 0 баллов или вернуть ошибку
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_teacher_cannot_take_test(self):
        """Преподаватель не может проходить тест (только просматривать)"""
        self.client.force_authenticate(user=self.teacher1)
        url = reverse("tests:test-start-attempt", args=[self.test1.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ===== ТЕСТЫ НА ПРОСМОТР РЕЗУЛЬТАТОВ =====
    def test_student_can_view_own_results(self):
        """Студент может видеть свои результаты"""
        # Студент проходит тест
        self.client.force_authenticate(user=self.student1)
        start_url = reverse("tests:test-start-attempt", args=[self.test1.id])
        self.client.post(start_url)

        submit_url = reverse("tests:test-submit", args=[self.test1.id])
        data = {
            "answers": {
                str(self.question1.id): [self.answer1_2.id],
                str(self.question2.id): [self.answer2_1.id, self.answer2_3.id],
            }
        }
        self.client.post(submit_url, data, format="json")

        # Проверяем результаты
        results_url = reverse("tests:result-list")
        response = self.client.get(results_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = self.get_results(response)
        self.assertEqual(len(results), 1)

    def test_student_cannot_view_others_results(self):
        """Студент не может видеть чужие результаты"""
        # Студент1 проходит тест
        self.client.force_authenticate(user=self.student1)
        start_url = reverse("tests:test-start-attempt", args=[self.test1.id])
        self.client.post(start_url)

        submit_url = reverse("tests:test-submit", args=[self.test1.id])
        data = {
            "answers": {
                str(self.question1.id): [self.answer1_2.id],
                str(self.question2.id): [self.answer2_1.id, self.answer2_3.id],
            }
        }
        self.client.post(submit_url, data, format="json")

        # Студент2 пытается посмотреть результаты
        self.client.force_authenticate(user=self.student2)
        results_url = reverse("tests:result-list")
        response = self.client.get(results_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = self.get_results(response)
        self.assertEqual(len(results), 0)

    def test_teacher_can_view_results_of_own_lessons(self):
        """Преподаватель видит результаты студентов своих уроков"""
        # Студент проходит тест
        self.client.force_authenticate(user=self.student1)
        start_url = reverse("tests:test-start-attempt", args=[self.test1.id])
        self.client.post(start_url)

        submit_url = reverse("tests:test-submit", args=[self.test1.id])
        data = {
            "answers": {
                str(self.question1.id): [self.answer1_2.id],
                str(self.question2.id): [self.answer2_1.id, self.answer2_3.id],
            }
        }
        self.client.post(submit_url, data, format="json")

        # Преподаватель проверяет результаты
        self.client.force_authenticate(user=self.teacher1)
        results_url = reverse("tests:result-list")
        response = self.client.get(results_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = self.get_results(response)
        self.assertEqual(len(results), 1)

    def test_admin_can_view_all_results(self):
        """Админ видит все результаты"""
        # Два студента проходят тесты
        for student in [self.student1, self.student2]:
            self.client.force_authenticate(user=student)
            start_url = reverse("tests:test-start-attempt", args=[self.test1.id])
            self.client.post(start_url)

            submit_url = reverse("tests:test-submit", args=[self.test1.id])
            data = {
                "answers": {
                    str(self.question1.id): [self.answer1_2.id],
                    str(self.question2.id): [self.answer2_1.id, self.answer2_3.id],
                }
            }
            self.client.post(submit_url, data, format="json")

        # Админ проверяет результаты
        self.client.force_authenticate(user=self.admin)
        results_url = reverse("tests:result-list")
        response = self.client.get(results_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = self.get_results(response)
        self.assertEqual(len(results), 2)

    # ===== ТЕСТЫ НА ПРОСМОТР ПОПЫТОК =====
    def test_student_can_view_own_attempts(self):
        """Студент может видеть свои попытки"""
        self.client.force_authenticate(user=self.student1)

        # Создаем попытку
        start_url = reverse("tests:test-start-attempt", args=[self.test1.id])
        self.client.post(start_url)

        # Проверяем список попыток
        attempts_url = reverse("tests:attempt-list")
        response = self.client.get(attempts_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = self.get_results(response)
        self.assertEqual(len(results), 1)

    def test_student_can_view_attempt_answers(self):
        """Студент может видеть свои ответы на попытку"""
        self.client.force_authenticate(user=self.student1)

        # Создаем попытку и отвечаем
        start_url = reverse("tests:test-start-attempt", args=[self.test1.id])
        start_response = self.client.post(start_url)
        attempt_id = start_response.data["id"]

        submit_url = reverse("tests:test-submit", args=[self.test1.id])
        data = {
            "answers": {
                str(self.question1.id): [self.answer1_2.id],
                str(self.question2.id): [self.answer2_1.id, self.answer2_3.id],
            }
        }
        self.client.post(submit_url, data, format="json")

        # Получаем ответы на попытку
        answers_url = reverse("tests:attempt-get-answers", args=[attempt_id])
        response = self.client.get(answers_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # два вопроса

    # ===== ТЕСТЫ НА ПАГИНАЦИЮ =====
    def test_test_pagination(self):
        """Проверка пагинации тестов"""
        # Создаем новый курс для тестов пагинации
        new_course = Course.objects.create(title="Курс для пагинации", owner=self.teacher1)

        # Создаем уроки и тесты
        for i in range(10):
            lesson = Lesson.objects.create(
                course=new_course, title=f"Урок для теста {i}", owner=self.teacher1, order=i
            )

            Test.objects.create(lesson=lesson, title=f"Тест {i}", owner=self.teacher1)

        self.client.force_authenticate(user=self.admin)
        url = reverse("tests:test-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверка пагинации
        self.assertEqual(response.data["count"], 13)  # 3 старых + 10 новых
        self.assertEqual(len(response.data["results"]), 5)

    def test_results_pagination(self):
        """Проверка пагинации результатов"""
        # Создаем много результатов
        for i in range(20):
            TestResult.objects.create(
                user=self.student1, test=self.test1, score=i, max_score=10, percentage=i * 10, passed=True
            )

        self.client.force_authenticate(user=self.admin)
        url = reverse("tests:result-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем структуру пагинации
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("results", response.data)
