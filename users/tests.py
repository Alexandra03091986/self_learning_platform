from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from courses.models import Course, Lesson
from tests.models import Test, TestAttempt

from .models import User


class UserAPITestCase(APITestCase):
    """Тесты для API пользователей"""

    def setUp(self):
        """Подготовка данных перед каждым тестом"""
        # Создаем пользователей разных ролей
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

        self.student1 = User.objects.create_user(
            username="student1",
            email="student1@test.com",
            password="studentpass123",
            role="student",
            first_name="Мария",
            last_name="Сидорова",
        )

        self.student2 = User.objects.create_user(
            username="student2",
            email="student2@test.com",
            password="studentpass123",
            role="student",
            first_name="Петр",
            last_name="Иванов",
        )

    def get_results(self, response):
        """Получить результаты из ответа с учетом пагинации"""
        if isinstance(response.data, dict) and "results" in response.data:
            return response.data["results"]
        return response.data

    def test_user_registration(self):
        """Тест регистрации пользователя"""
        url = reverse("users:register")
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "first_name": "Test",
            "last_name": "User",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 5)
        # Находим созданного пользователя по username
        new_user = User.objects.get(username="testuser")
        self.assertEqual(new_user.role, "student")  # роль по умолчанию
        self.assertEqual(new_user.email, "test@example.com")
        self.assertEqual(new_user.first_name, "Test")
        self.assertEqual(new_user.last_name, "User")
        # Проверяем, что админ остался админом
        admin = User.objects.get(username="admin")
        self.assertEqual(admin.role, "admin")

    def test_user_registration_password_mismatch(self):
        """Ошибка при несовпадении паролей"""
        url = reverse("users:register")
        data = {
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "password123",
            "password_confirm": "different123",
            "first_name": "Новый",
            "last_name": "Пользователь",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Пароли не совпадают", str(response.data))

    def test_user_registration_duplicate_username(self):
        """Ошибка при регистрации с существующим username"""
        url = reverse("users:register")
        data = {
            "username": "student1",  # уже существующий
            "email": "new@test.com",
            "password": "password123",
            "password_confirm": "password123",
            "first_name": "Новый",
            "last_name": "Пользователь",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("уже существует", str(response.data))

    def test_user_registration_duplicate_email(self):
        """Ошибка при регистрации с существующим email"""
        url = reverse("users:register")
        data = {
            "username": "newuser",
            "email": "student1@test.com",  # уже существующий
            "password": "password123",
            "password_confirm": "password123",
            "first_name": "Новый",
            "last_name": "Пользователь",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("уже существует", str(response.data))

    def test_user_registration_missing_required_fields(self):
        """Ошибка при отсутствии обязательных полей"""
        url = reverse("users:register")
        data = {
            "username": "newuser",
            "password": "password123",
            "password_confirm": "password123",
            # нет first_name, last_name, email
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ===== ТЕСТЫ ВХОДА =====
    def test_user_login_success_with_email(self):
        """Успешный вход по email"""
        url = reverse("users:login")
        data = {"email": "student1@test.com", "password": "studentpass123"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], "student1@test.com")

    def test_user_login_wrong_password(self):
        """Ошибка при неверном пароле"""
        url = reverse("users:login")
        data = {"email": "student1@test.com", "password": "wrongpassword"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Неверный пароль", str(response.data))

    def test_user_login_nonexistent_email(self):
        """Ошибка при входе с несуществующим email"""
        url = reverse("users:login")
        data = {"email": "nonexistent@test.com", "password": "password123"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("не найден", str(response.data))

    def test_user_login_missing_email(self):
        """Ошибка при отсутствии email"""
        url = reverse("users:login")
        data = {"password": "password123"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ===== ТЕСТЫ СПИСКА ПОЛЬЗОВАТЕЛЕЙ (UserListView) =====
    def test_admin_can_view_all_users(self):
        """Администратор может видеть всех пользователей"""
        self.client.force_authenticate(user=self.admin)
        url = reverse("users:user-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = self.get_results(response)
        self.assertEqual(len(results), 4)

    def test_student_cannot_view_all_users(self):
        """Студент НЕ может видеть список всех пользователей"""
        self.client.force_authenticate(user=self.student1)
        url = reverse("users:user-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_view_users(self):
        """Неавторизованный пользователь НЕ может видеть список пользователей"""
        url = reverse("users:user-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list_pagination(self):
        """Проверка пагинации списка пользователей"""
        self.client.force_authenticate(user=self.admin)
        url = reverse("users:user-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем структуру пагинации
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 4)

    # ===== ТЕСТЫ ДЕТАЛЬНОГО ПРОСМОТРА ПОЛЬЗОВАТЕЛЯ (UserDetailView) =====
    def test_admin_can_view_any_user(self):
        """Администратор может просматривать любого пользователя"""
        self.client.force_authenticate(user=self.admin)
        url = reverse("users:user-detail", args=[self.student1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "student1")

    def test_student_can_view_own_profile(self):
        """Студент может просматривать свой профиль"""
        self.client.force_authenticate(user=self.student1)
        url = reverse("users:user-detail", args=[self.student1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "student1")

    def test_student_cannot_view_other_profile(self):
        """Студент НЕ может просматривать чужой профиль"""
        self.client.force_authenticate(user=self.student1)
        url = reverse("users:user-detail", args=[self.student2.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_cannot_view_profile(self):
        """Неавторизованный пользователь НЕ может просматривать профиль"""
        url = reverse("users:user-detail", args=[self.student1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ===== ТЕСТЫ ОБНОВЛЕНИЯ ПОЛЬЗОВАТЕЛЯ =====
    def test_admin_can_update_any_user(self):
        """Администратор может обновлять любого пользователя"""
        self.client.force_authenticate(user=self.admin)
        url = reverse("users:user-detail", args=[self.student1.id])
        data = {"first_name": "Обновленное", "last_name": "Имя"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.student1.refresh_from_db()
        self.assertEqual(self.student1.first_name, "Обновленное")
        self.assertEqual(self.student1.last_name, "Имя")

    def test_admin_can_change_user_role(self):
        """Администратор может менять роль пользователя"""
        self.client.force_authenticate(user=self.admin)
        url = reverse("users:user-detail", args=[self.student1.id])
        data = {"role": "teacher"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.student1.refresh_from_db()
        self.assertEqual(self.student1.role, "teacher")

    def test_teacher_cannot_update_user(self):
        """Преподаватель НЕ может обновлять пользователей"""
        self.client.force_authenticate(user=self.teacher)
        url = reverse("users:user-detail", args=[self.student1.id])
        data = {"first_name": "Обновленное"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_update_own_profile(self):
        """Студент НЕ может обновлять даже свой профиль"""
        self.client.force_authenticate(user=self.student1)
        url = reverse("users:user-detail", args=[self.student1.id])
        data = {"first_name": "Обновленное"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ===== ТЕСТЫ УДАЛЕНИЯ ПОЛЬЗОВАТЕЛЯ =====
    def test_admin_can_delete_user(self):
        """Администратор может удалить пользователя"""
        self.client.force_authenticate(user=self.admin)
        url = reverse("users:user-detail", args=[self.student1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(User.objects.count(), 3)

    def test_teacher_cannot_delete_user(self):
        """Преподаватель НЕ может удалить пользователя"""
        self.client.force_authenticate(user=self.teacher)
        url = reverse("users:user-detail", args=[self.student1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_delete_user(self):
        """Студент НЕ может удалить пользователя"""
        self.client.force_authenticate(user=self.student1)
        url = reverse("users:user-detail", args=[self.student2.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CourseStudentsViewTests(APITestCase):
    """Тесты для просмотра студентов курса"""

    def setUp(self):
        """Подготовка тестовых данных"""
        # Создаем пользователей
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
            first_name="Мария",
            last_name="Иванова",
        )

        self.student1 = User.objects.create_user(
            username="student1",
            email="student1@test.com",
            password="studentpass123",
            role="student",
            first_name="Петр",
            last_name="Сидоров",
        )

        self.student2 = User.objects.create_user(
            username="student2",
            email="student2@test.com",
            password="studentpass123",
            role="student",
            first_name="Анна",
            last_name="Смирнова",
        )

        self.student3 = User.objects.create_user(
            username="student3",
            email="student3@test.com",
            password="studentpass123",
            role="student",
            first_name="Ольга",
            last_name="Козлова",
        )

        # Создаем курсы
        self.course1 = Course.objects.create(title="Курс 1", description="Описание курса 1", owner=self.teacher1)

        self.course2 = Course.objects.create(title="Курс 2", description="Описание курса 2", owner=self.teacher2)

        # Создаем уроки
        self.lesson1 = Lesson.objects.create(course=self.course1, title="Урок 1", owner=self.teacher1, order=1)

        self.lesson2 = Lesson.objects.create(course=self.course2, title="Урок 2", owner=self.teacher2, order=1)

        # Создаем тесты
        self.test1 = Test.objects.create(lesson=self.lesson1, title="Тест 1", owner=self.teacher1)

        self.test2 = Test.objects.create(lesson=self.lesson2, title="Тест 2", owner=self.teacher2)

        # Создаем попытки прохождения тестов
        # Student1 проходит тест на курсе 1
        self.attempt1 = TestAttempt.objects.create(test=self.test1, user=self.student1, status="completed")

        # Student2 проходит тест на курсе 1
        self.attempt2 = TestAttempt.objects.create(test=self.test1, user=self.student2, status="completed")

        # Student3 проходит тест на курсе 2
        self.attempt3 = TestAttempt.objects.create(test=self.test2, user=self.student3, status="completed")

    def test_teacher_can_view_his_course_students(self):
        """Преподаватель может видеть студентов своего курса"""
        self.client.force_authenticate(user=self.teacher1)
        url = reverse("users:course-students", kwargs={"course_id": self.course1.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Должен видеть student1 и student2

        # Проверяем, что видит только студентов
        student_emails = [user["email"] for user in response.data]
        self.assertIn("student1@test.com", student_emails)
        self.assertIn("student2@test.com", student_emails)
        self.assertNotIn("student3@test.com", student_emails)  # Студент с другого курса
        self.assertNotIn("teacher1@test.com", student_emails)  # Не видит преподавателей

    def test_teacher_cannot_view_other_course_students(self):
        """Преподаватель НЕ может видеть студентов чужого курса"""
        self.client.force_authenticate(user=self.teacher1)  # teacher1 пытается посмотреть курс teacher2
        url = reverse("users:course-students", kwargs={"course_id": self.course2.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # Пустой список

    def test_student_cannot_view_course_students(self):
        """Студент НЕ может видеть список студентов курса"""
        self.client.force_authenticate(user=self.student1)
        url = reverse("users:course-students", kwargs={"course_id": self.course1.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # Пустой список

    def test_teacher_cannot_view_all_users(self):
        """Преподаватель НЕ может видеть список всех пользователей"""
        self.client.force_authenticate(user=self.teacher1)
        url = reverse("users:user-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_can_view_own_profile(self):
        """Преподаватель может просматривать свой профиль"""
        self.client.force_authenticate(user=self.teacher1)
        url = reverse("users:user-detail", args=[self.teacher1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "teacher1")
