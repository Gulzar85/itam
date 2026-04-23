import uuid

from django.test import TestCase
from django.urls import reverse

from accounts.models import Department, User


class DepartmentModelTest(TestCase):
    def test_department_creation(self):
        dept = Department.objects.create(name="Engineering")
        self.assertEqual(str(dept), "Engineering")

    def test_department_unique_name(self):
        Department.objects.create(name="IT")
        with self.assertRaises(Exception):
            Department.objects.create(name="IT")


class UserModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.department = Department.objects.create(name="IT")

    def test_user_creation_employee(self):
        user = User.objects.create_user(
            username="employee",
            email="employee@example.com",
            password="pass123",
            role=User.IS_EMPLOYEE,
            department=self.department,
        )
        self.assertEqual(user.role, User.IS_EMPLOYEE)
        self.assertTrue(user.check_password("pass123"))

    def test_user_creation_manager(self):
        user = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="pass123",
            role=User.IS_MANAGER,
            department=self.department,
        )
        self.assertEqual(user.role, User.IS_MANAGER)

    def test_user_creation_it_admin(self):
        user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="pass123",
            role=User.IS_IT_ADMIN,
            department=self.department,
            is_staff=True,
        )
        self.assertEqual(user.role, User.IS_IT_ADMIN)
        self.assertTrue(user.is_staff)

    def test_user_uuid_primary_key(self):
        user = User.objects.create_user(
            username="uuiduser",
            email="uuid@example.com",
            password="pass123",
            role=User.IS_EMPLOYEE,
        )
        self.assertIsInstance(user.id, uuid.UUID)

    def test_user_manager_relationship(self):
        manager = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="pass123",
            role=User.IS_MANAGER,
        )
        employee = User.objects.create_user(
            username="employee",
            email="employee@example.com",
            password="pass123",
            role=User.IS_EMPLOYEE,
            manager=manager,
        )
        self.assertEqual(employee.manager, manager)
        self.assertIn(employee, manager.team_members.all())

    def test_is_line_manager_property(self):
        manager = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="pass123",
            role=User.IS_MANAGER,
        )
        self.assertFalse(manager.is_line_manager)

        User.objects.create_user(
            username="employee",
            email="employee@example.com",
            password="pass123",
            role=User.IS_EMPLOYEE,
            manager=manager,
        )
        manager.refresh_from_db()
        self.assertTrue(manager.is_line_manager)


class AuthViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.department = Department.objects.create(name="IT")
        cls.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role=User.IS_EMPLOYEE,
            department=cls.department,
        )

    def test_login_view_get(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)

    def test_login_success(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "testuser", "password": "testpass123"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["user"].is_authenticated)

    def test_login_failure(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "testuser", "password": "wrongpassword"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())

    def test_logout(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 302)
