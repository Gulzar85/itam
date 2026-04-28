"""
Comprehensive tests for accounts app
"""
import uuid
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import IntegrityError

from accounts.models import Department

User = get_user_model()


class DepartmentModelTest(TestCase):
    """Tests for Department model"""

    def setUp(self):
        self.department = Department.objects.create(name="IT Department")

    def test_department_creation(self):
        """Test department can be created"""
        self.assertEqual(self.department.name, "IT Department")
        self.assertIsInstance(self.department.id, uuid.UUID)

    def test_department_str(self):
        """Test string representation"""
        self.assertEqual(str(self.department), "IT Department")

    def test_department_unique_name(self):
        """Test department name must be unique"""
        with self.assertRaises(IntegrityError):
            Department.objects.create(name="IT Department")

    def test_department_name_max_length(self):
        """Test department name field max length"""
        dept = Department._meta.get_field('name')
        self.assertEqual(dept.max_length, 100)


class UserModelTest(TestCase):
    """Tests for custom User model"""

    def setUp(self):
        self.department = Department.objects.create(name="HR")
        self.manager = User.objects.create_user(
            username="manager1",
            email="manager@test.com",
            password="testpass123",
            role="IT_ADMIN"
        )
        self.employee = User.objects.create_user(
            username="employee1",
            email="employee@test.com",
            password="testpass123",
            role="EMPLOYEE",
            department=self.department,
            manager=self.manager
        )

    def test_user_creation(self):
        """Test user can be created with custom fields"""
        self.assertEqual(self.employee.role, "EMPLOYEE")
        self.assertEqual(self.employee.department, self.department)
        self.assertEqual(self.employee.manager, self.manager)
        self.assertIsInstance(self.employee.id, uuid.UUID)

    def test_user_str(self):
        """Test string representation"""
        expected = "employee1 (EMPLOYEE)"
        self.assertEqual(str(self.employee), expected)

    def test_user_email_unique(self):
        """Test email must be unique"""
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username="employee2",
                email="employee@test.com",  # Duplicate email
                password="testpass123"
            )

    def test_is_manager_property(self):
        """Test is_manager property"""
        self.assertTrue(self.manager.is_manager)
        self.assertFalse(self.employee.is_manager)

    def test_can_approve_property(self):
        """Test can_approve property"""
        self.assertTrue(self.manager.can_approve)  # Manager with team members
        self.assertFalse(self.employee.can_approve)

    def test_it_admin_can_approve(self):
        """Test IT admin can approve regardless of team"""
        self.assertTrue(self.manager.can_approve)

    def test_get_full_name(self):
        """Test get_full_name method exists"""
        self.employee.first_name = "John"
        self.employee.last_name = "Doe"
        self.employee.save()
        self.assertEqual(self.employee.get_full_name(), "John Doe")


class UserProfileFormTest(TestCase):
    """Tests for UserProfileForm"""

    def setUp(self):
        self.department = Department.objects.create(name="IT")
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123",
            department=self.department
        )

    def test_form_valid_data(self):
        """Test form with valid data"""
        from accounts.forms import UserProfileForm
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@test.com',
            'phone_number': '+1234567890',
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_form_invalid_email(self):
        """Test form with invalid email"""
        from accounts.forms import UserProfileForm
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'invalid-email',
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())


class AccountsViewsTest(TestCase):
    """Tests for accounts views"""

    def setUp(self):
        self.department = Department.objects.create(name="IT")
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123",
            role="EMPLOYEE",
            department=self.department
        )

    def test_profile_view_requires_login(self):
        """Test profile view redirects if not logged in"""
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)

    def test_profile_view_logged_in(self):
        """Test profile view accessible when logged in"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)

    def test_profile_edit_view(self):
        """Test profile edit view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('accounts:profile_edit'))
        self.assertEqual(response.status_code, 200)

    def test_profile_edit_post(self):
        """Test profile edit POST request"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('accounts:profile_edit'), {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@test.com',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')

    def test_change_password_view(self):
        """Test change password view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('accounts:change_password'))
        self.assertEqual(response.status_code, 200)
