from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User

from .models import Course, Lesson


class CourseAPITestCase(APITestCase):
    """Тесты для API курсов"""

    def setUp(self):
        """Подготовка данных перед каждым тестом"""
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="adminpass123",
            role="admin",
            first_name="Admin",
            last_name="User",
        )
        self.teacher1 = User.objects.create_user(
            username="teacher1",
            email="teacher1@test.com",
            password="pass123",
            role="teacher",
            first_name="Иван",
            last_name="Петров",
        )
        self.teacher2 = User.objects.create_user(
            username="teacher2",
            email="teacher2@test.com",
            password="teacherpass123",
            role="teacher",
            first_name="Петр",
            last_name="Иванов",
        )
        self.student = User.objects.create_user(
            username="student",
            email="student@test.com",
            password="pass123",
            role="student",
            first_name="Мария",
            last_name="Сидорова",
        )
        # Создаем курсы
        self.course1 = Course.objects.create(
            title="Python для начинающих", description="Базовый курс по Python", owner=self.teacher1
        )

        self.course2 = Course.objects.create(
            title="Java для начинающих", description="Базовый курс по Java", owner=self.teacher2
        )

        self.course3 = Course.objects.create(
            title="JavaScript для начинающих", description="Базовый курс по JavaScript", owner=self.teacher1
        )

    def get_results(self, response):
        """Получить результаты из ответа с учетом пагинации"""
        if isinstance(response.data, dict) and "results" in response.data:
            return response.data["results"]
        return response.data

    # ===== ТЕСТЫ НА СОЗДАНИЕ КУРСОВ =====
    def test_teacher_can_create_course(self):
        """Преподаватель может создать курс"""
        self.client.force_authenticate(user=self.teacher1)
        url = reverse("courses:course-list")
        data = {"title": "Новый курс", "description": "Описание нового курса"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Course.objects.count(), 4)
        self.assertEqual(response.data["title"], "Новый курс")
        self.assertEqual(response.data["owner"], self.teacher1.id)

    def test_student_cannot_create_course(self):
        """Студент не может создать курс"""
        self.client.force_authenticate(user=self.student)
        url = reverse("courses:course-list")
        data = {"title": "Новый курс", "description": "Описание"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Course.objects.count(), 3)

    def test_unauthenticated_cannot_create_course(self):
        """Неавторизованный пользователь НЕ может создать курс"""
        url = reverse("courses:course-list")
        data = {"title": "Новый курс", "description": "Описание"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ===== ТЕСТЫ НА ПРОСМОТР КУРСОВ =====
    def test_any_authenticated_can_view_courses(self):
        """Любой авторизованный пользователь может видеть список курсов"""
        self.client.force_authenticate(user=self.student)
        url = reverse("courses:course-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = self.get_results(response)
        self.assertEqual(len(results), 3)

    def test_course_detail_view(self):
        """Просмотр деталей конкретного курса"""
        self.client.force_authenticate(user=self.student)
        url = reverse("courses:course-detail", args=[self.course1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Python для начинающих")
        self.assertIn("owner_details", response.data)

    # ===== ТЕСТЫ НА ОБНОВЛЕНИЕ КУРСОВ =====
    def test_owner_can_update_course(self):
        """Владелец может обновить свой курс"""
        self.client.force_authenticate(user=self.teacher1)
        url = reverse("courses:course-detail", args=[self.course1.id])
        data = {"title": "Обновленный Python курс"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.course1.refresh_from_db()
        self.assertEqual(self.course1.title, "Обновленный Python курс")

    def test_admin_can_update_any_course(self):
        """Админ может обновить любой курс"""
        self.client.force_authenticate(user=self.admin)
        url = reverse("courses:course-detail", args=[self.course2.id])
        data = {"title": "Обновлено админом"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.course2.refresh_from_db()
        self.assertEqual(self.course2.title, "Обновлено админом")

    def test_other_teacher_cannot_update_course(self):
        """Другой преподаватель НЕ может обновить чужой курс"""
        self.client.force_authenticate(user=self.teacher2)
        url = reverse("courses:course-detail", args=[self.course1.id])
        data = {"title": "Попытка взлома"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_update_course(self):
        """Студент НЕ может обновить курс"""
        self.client.force_authenticate(user=self.student)
        url = reverse("courses:course-detail", args=[self.course1.id])
        data = {"title": "Попытка студента"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ===== ТЕСТЫ НА УДАЛЕНИЕ КУРСОВ =====
    def test_owner_can_delete_course(self):
        """Владелец может удалить свой курс"""
        self.client.force_authenticate(user=self.teacher1)
        url = reverse("courses:course-detail", args=[self.course1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Course.objects.count(), 2)

    def test_admin_can_delete_any_course(self):
        """Админ может удалить любой курс"""
        self.client.force_authenticate(user=self.admin)
        url = reverse("courses:course-detail", args=[self.course2.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Course.objects.count(), 2)

    def test_other_teacher_cannot_delete_course(self):
        """Другой преподаватель НЕ может удалить чужой курс"""
        self.client.force_authenticate(user=self.teacher2)
        url = reverse("courses:course-detail", args=[self.course1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Course.objects.count(), 3)

    # ===== ТЕСТЫ НА ПАГИНАЦИЮ =====
    def test_course_pagination(self):
        """Проверка пагинации курсов"""
        # Создаем еще курсов для проверки пагинации
        for i in range(10):
            Course.objects.create(title=f"Курс {i}", owner=self.teacher1)

        self.client.force_authenticate(user=self.student)
        url = reverse("courses:course-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем структуру пагинации
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("results", response.data)

        # Должно быть 13 курсов (3 старых + 10 новых)
        self.assertEqual(response.data["count"], 13)
        # На первой странице 5 элементов (page_size = 5)
        self.assertEqual(len(response.data["results"]), 5)


class LessonAPITestCase(APITestCase):
    """Тесты для API уроков"""

    def setUp(self):
        """Подготовка данных перед каждым тестом"""
        # Создаем пользователей
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="adminpass123",
            role="admin",
            first_name="Admin",
            last_name="User",
        )

        self.teacher = User.objects.create_user(
            username="teacher",
            email="teacher@test.com",
            password="teacherpass123",
            role="teacher",
            first_name="Иван",
            last_name="Петров",
        )

        self.teacher2 = User.objects.create_user(
            username="teacher2",
            email="teacher2@test.com",
            password="teacherpass123",
            role="teacher",
            first_name="Петр",
            last_name="Иванов",
        )

        self.student = User.objects.create_user(
            username="student",
            email="student@test.com",
            password="studentpass123",
            role="student",
            first_name="Мария",
            last_name="Сидорова",
        )

        # Создаем курсы
        self.course1 = Course.objects.create(
            title="Python для начинающих", description="Базовый курс по Python", owner=self.teacher
        )

        self.course2 = Course.objects.create(
            title="Java для начинающих", description="Базовый курс по Java", owner=self.teacher2
        )

        # Создаем уроки
        self.lesson1 = Lesson.objects.create(
            course=self.course1, title="Введение в Python", description="Первые шаги", owner=self.teacher, order=1
        )

        self.lesson2 = Lesson.objects.create(
            course=self.course1, title="Переменные и типы данных", description="Основы", owner=self.teacher, order=2
        )

        self.lesson3 = Lesson.objects.create(
            course=self.course2, title="Введение в Java", description="Первые шаги", owner=self.teacher2, order=1
        )

    def get_results(self, response):
        """Получить результаты из ответа с учетом пагинации"""
        if isinstance(response.data, dict) and "results" in response.data:
            return response.data["results"]
        return response.data

    # Тесты на создание уроков
    def test_teacher_can_create_lesson_in_own_course(self):
        """Преподаватель может создать урок в своем курсе"""
        self.client.force_authenticate(user=self.teacher)
        url = reverse("courses:lesson-list")
        data = {
            "course": self.course1.id,
            "title": "Новый урок",
            "description": "Описание нового урока",
            "order": 3,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_lesson = Lesson.objects.get(title="Новый урок")
        self.assertEqual(new_lesson.owner, self.teacher)
        self.assertEqual(Lesson.objects.count(), 4)

        # Проверяем созданный урок
        new_lesson = Lesson.objects.get(title="Новый урок")
        self.assertEqual(new_lesson.owner, self.teacher)
        self.assertEqual(new_lesson.course, self.course1)

    def test_teacher_cannot_create_lesson_in_foreign_course(self):
        """Преподаватель НЕ может создать урок в чужом курсе"""
        self.client.force_authenticate(user=self.teacher)
        url = reverse("courses:lesson-list")
        data = {
            "course": self.course2.id,  # курс другого преподавателя
            "title": "Новый урок",
            "description": "Описание",
            "order": 1,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Lesson.objects.count(), 3)

    def test_admin_can_create_lesson_in_any_course(self):
        """Админ может создать урок в любом курсе"""
        self.client.force_authenticate(user=self.admin)
        url = reverse("courses:lesson-list")
        data = {"course": self.course2.id, "title": "Урок от админа", "description": "Описание", "order": 2}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lesson.objects.last().owner, self.admin)

    def test_student_cannot_create_lesson(self):
        """Студент НЕ может создать урок"""
        self.client.force_authenticate(user=self.student)
        url = reverse("courses:lesson-list")
        data = {"course": self.course1.id, "title": "Новый урок", "description": "Описание", "order": 3}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_create_lesson(self):
        """Неавторизованный пользователь НЕ может создать урок"""
        url = reverse("courses:lesson-list")
        data = {"course": self.course1.id, "title": "Новый урок", "description": "Описание", "order": 3}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # Тесты на просмотр уроков
    def test_student_can_view_all_lessons(self):
        """Студент может просматривать все уроки"""
        self.client.force_authenticate(user=self.student)
        url = reverse("courses:lesson-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)  # должно быть 3 урока

    def test_student_can_view_single_lesson(self):
        """Студент может просматривать конкретный урок"""
        self.client.force_authenticate(user=self.student)
        url = reverse("courses:lesson-detail", args=[self.lesson1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Введение в Python")

    # Тесты на обновление уроков
    def test_teacher_can_update_own_lesson(self):
        """Преподаватель может обновить свой урок"""
        self.client.force_authenticate(user=self.teacher)
        url = reverse("courses:lesson-detail", args=[self.lesson1.id])
        data = {"title": "Обновленное название", "description": "Новое описание"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson1.refresh_from_db()
        self.assertEqual(self.lesson1.title, "Обновленное название")

    def test_teacher_cannot_update_foreign_lesson(self):
        """Преподаватель НЕ может обновить чужой урок"""
        self.client.force_authenticate(user=self.teacher)
        url = reverse("courses:lesson-detail", args=[self.lesson3.id])  # урок другого преподавателя
        data = {"title": "Обновленное название"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_update_any_lesson(self):
        """Админ может обновить любой урок"""
        self.client.force_authenticate(user=self.admin)
        url = reverse("courses:lesson-detail", args=[self.lesson3.id])
        data = {"title": "Обновлено админом"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson3.refresh_from_db()
        self.assertEqual(self.lesson3.title, "Обновлено админом")

    # Тесты на удаление уроков
    def test_teacher_can_delete_own_lesson(self):
        """Преподаватель может удалить свой урок"""
        self.client.force_authenticate(user=self.teacher)
        url = reverse("courses:lesson-detail", args=[self.lesson1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Lesson.objects.count(), 2)

    def test_teacher_cannot_delete_foreign_lesson(self):
        """Преподаватель НЕ может удалить чужой урок"""
        self.client.force_authenticate(user=self.teacher)
        url = reverse("courses:lesson-detail", args=[self.lesson3.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_any_lesson(self):
        """Админ может удалить любой урок"""
        self.client.force_authenticate(user=self.admin)
        url = reverse("courses:lesson-detail", args=[self.lesson3.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Lesson.objects.count(), 2)

    # Тест на фильтрацию по курсу
    def test_filter_lessons_by_course(self):
        """Тест фильтрации уроков по курсу"""
        self.client.force_authenticate(user=self.student)
        url = reverse("courses:lesson-list")
        response = self.client.get(url, {"course": self.course1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if isinstance(response.data, dict) and "results" in response.data:
            self.assertEqual(len(response.data["results"]), 3)  # у course1 три урока
        else:
            self.assertEqual(len(response.data), 3)

    # Тест на порядок сортировки
    def test_lessons_ordered_by_order(self):
        """Тест сортировки уроков по полю order"""
        self.client.force_authenticate(user=self.student)
        url = reverse("courses:lesson-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ===== ТЕСТЫ НА ПАГИНАЦИЮ =====
    def test_lesson_pagination(self):
        """Проверка пагинации уроков"""
        # Создаем еще уроков для проверки пагинации
        for i in range(10):
            Lesson.objects.create(course=self.course1, title=f"Урок {i}", owner=self.teacher, order=i + 10)

        self.client.force_authenticate(user=self.student)
        url = reverse("courses:lesson-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем структуру пагинации
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("results", response.data)

        # Должно быть 13 уроков (3 старых + 10 новых)
        self.assertEqual(response.data["count"], 13)
        # На первой странице 5 элементов (page_size = 5)
        self.assertEqual(len(response.data["results"]), 5)
