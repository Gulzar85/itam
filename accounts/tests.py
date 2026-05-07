"""
Tests for accounts app
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client
from accounts.models import Department
import uuid

User = get_user_model()


class UserModelTest(TestCase):
    """Test the custom User model"""

    def setUp(self):
        self.department = Department.objects.create(name='IT Department')
        self.manager = User.objects.create_user(
            username='manager1',
            email='manager@test.com',
            password='testpass123',
            role=User.IS_IT_ADMIN,
            department=self.department
        )
        self.user = User.objects.create_user(
            username='employee1',
            email='employee@test.com',
            password='testpass123',
            role=User.IS_EMPLOYEE,
            department=self.department,
            manager=self.manager
        )

    def test_user_creation(self):
        """Test user creation with custom fields"""
        self.assertEqual(self.user.username, 'employee1')
        self.assertEqual(self.user.role, User.IS_EMPLOYEE)
        self.assertEqual(self.user.department, self.department)
        self.assertEqual(self.user.manager, self.manager)

    def test_user_str_representation(self):
        """Test string representation of User"""
        expected = f"{self.user.username} ({self.user.role})"
        self.assertEqual(str(self.user), expected)

    def test_is_manager_property(self):
        """Test is_manager property"""
        self.assertTrue(self.manager.is_manager)
        self.assertFalse(self.user.is_manager)

    def test_can_approve_property(self):
        """Test can_approve property"""
        self.assertTrue(self.manager.can_approve)
        self.assertFalse(self.user.can_approve)

    def test_employee_without_department(self):
        """Test employee creation without department"""
        user = User.objects.create_user(
            username='employee2',
            email='employee2@test.com',
            password='testpass123',
            role=User.IS_EMPLOYEE
        )
        self.assertIsNone(user.department)
        self.assertFalse(user.is_manager)


class DepartmentModelTest(TestCase):
    """Test Department model"""

    def test_department_creation(self):
        dept = Department.objects.create(name='Finance')
        self.assertEqual(str(dept), 'Finance')
        self.assertEqual(dept.name, 'Finance')

    def test_department_unique_name(self):
        """Test department name uniqueness"""
        Department.objects.create(name='HR')
        with self.assertRaises(Exception):
            Department.objects.create(name='HR')


class ProfileViewTest(TestCase):
    """Test profile views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role=User.IS_EMPLOYEE
        )
        self.client.login(username='testuser', password='testpass123')

    def test_profile_detail_view(self):
        """Test profile detail view loads"""
        self.user.role = User.IS_EMPLOYEE
        self.user.save()
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')

    def test_profile_update_view(self):
        """Test profile update"""
        self.user.role = User.IS_EMPLOYEE
        self.user.save()
        response = self.client.post(reverse('accounts:profile_edit'), {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@test.com',
            'phone_number': '+1234567890',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')


class UserCreationFormTest(TestCase):
    """Test UserCreationForm"""

    def setUp(self):
        self.department = Department.objects.create(name='IT')

    def test_form_valid_data(self):
        from accounts.forms import UserCreationForm
        form_data = {
            'username': 'newuser',
            'email': 'new@test.com',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'EMPLOYEE',
            'department': self.department.id,
            'password1': 'complexpass123',
            'password2': 'complexpass123',
        }
        form = UserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_password_mismatch(self):
        """Test password mismatch validation"""
        from accounts.forms import UserCreationForm
        form_data = {
            'username': 'newuser',
            'email': 'new@test.com',
            'password1': 'pass1',
            'password2': 'pass2',
        }
        form = UserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)


class RegisterViewTest(TestCase):
    """Test user registration view (admin only)"""

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        # Superuser needs role set
        self.admin.role = User.IS_IT_ADMIN
        self.admin.save()

    def test_register_view_requires_admin(self):
        """Test that registration requires admin access"""
        response = self.client.get(reverse('accounts:register'))
        self.assertNotEqual(response.status_code, 200)

        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)
