"""
Tests for requests app
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from requests.models import Request, RequestLog, Assignment
from equipment.models import Equipment, Brand, Category, Vendor
from accounts.models import User, Department
from django.utils import timezone
from datetime import date
import uuid

User = get_user_model()


class RequestModelTest(TestCase):
    """Test Request model"""

    def setUp(self):
        self.department = Department.objects.create(name='IT')
        self.user = User.objects.create_user(
            username='employee',
            email='employee@test.com',
            password='test123',
            department=self.department,
            role=User.IS_EMPLOYEE
        )
        self.category = Category.objects.create(name='Laptop')
        self.brand = Brand.objects.create(name='Dell')

    def test_request_creation(self):
        """Test request creation"""
        request = Request.objects.create(
            user=self.user,
            request_type='NEW',
            priority='MEDIUM',
            category_needed=self.category,
            brand_preference=self.brand,
            reason='Need a new laptop for work',
            status='PENDING'
        )
        self.assertEqual(request.request_type, 'NEW')
        self.assertEqual(request.status, 'PENDING')
        self.assertIsNotNone(request.request_id)

    def test_request_str_representation(self):
        """Test string representation"""
        request = Request.objects.create(
            user=self.user,
            request_type='REPAIR',
            priority='HIGH',
            reason='Fix my laptop',
        )
        self.assertIn('REQ-', str(request))

    def test_generate_request_id(self):
        """Test request ID generation"""
        request = Request()
        request_id = request.generate_request_id()
        self.assertTrue(request_id.startswith('REQ-'))


class RequestFormTest(TestCase):
    """Test ITRequestForm"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='formuser',
            email='formuser@test.com',
            password='test123',
            role=User.IS_EMPLOYEE
        )
        self.category = Category.objects.create(name='Laptop')
        self.brand = Brand.objects.create(name='Dell')
        self.equipment = Equipment.objects.create(
            category=self.category,
            brand=self.brand,
            model_number='Test',
            serial_number='SN001',
            status='ASSIGNED',
            assigned_to=self.user
        )

    def test_form_valid_new_request(self):
        """Test form with valid new request data"""
        from requests.forms import ITRequestForm
        form_data = {
            'request_type': 'NEW',
            'priority': 'HIGH',
            'category_needed': self.category.id,
            'brand_preference': self.brand.id,
            'reason': 'Need a new laptop',
        }
        form = ITRequestForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_form_valid_repair_request(self):
        """Test form with valid repair request"""
        from requests.forms import ITRequestForm
        form_data = {
            'request_type': 'REPAIR',
            'priority': 'MEDIUM',
            'equipment': self.equipment.id,
            'reason': 'Laptop screen is broken',
        }
        form = ITRequestForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_form_repair_requires_equipment(self):
        """Test that repair request requires equipment"""
        from requests.forms import ITRequestForm
        form_data = {
            'request_type': 'REPAIR',
            'priority': 'LOW',
            'reason': 'Fix something',
        }
        form = ITRequestForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())

    def test_form_new_requires_category(self):
        """Test that new request requires category"""
        from requests.forms import ITRequestForm
        form_data = {
            'request_type': 'NEW',
            'priority': 'LOW',
            'reason': 'Need equipment',
        }
        form = ITRequestForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())


class RequestServiceTest(TestCase):
    """Test RequestService"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='serviceuser',
            email='service@test.com',
            password='test123',
            role=User.IS_EMPLOYEE
        )
        self.admin = User.objects.create_user(
            username='serviceadmin',
            email='serviceadmin@test.com',
            password='test123',
            role=User.IS_IT_ADMIN
        )
        self.category = Category.objects.create(name='Laptop')
        self.brand = Brand.objects.create(name='Dell')
        self.equipment = Equipment.objects.create(
            category=self.category,
            brand=self.brand,
            model_number='Test',
            serial_number='SN001',
            status='AVAILABLE'
        )

    def test_update_request_status(self):
        """Test request status update"""
        from services.request_service import RequestService

        request = Request.objects.create(
            user=self.user,
            request_type='NEW',
            priority='MEDIUM',
            category_needed=self.category,
            reason='Test request'
        )

        RequestService.update_request_status(
            request_obj=request,
            new_status='MANAGER_APPROVED',
            action_by=self.admin,
            remarks='Approved by admin'
        )

        request.refresh_from_db()
        self.assertEqual(request.status, 'MANAGER_APPROVED')

    def test_create_new_request_service(self):
        """Test create_new_request service method"""
        from services.request_service import RequestService

        request = RequestService.create_new_request(
            user=self.user,
            request_type='NEW',
            category=self.category,
            brand=self.brand,
            reason='Need new equipment'
        )

        self.assertIsNotNone(request.request_id)
        self.assertEqual(request.status, 'PENDING')


class RequestWorkflowTest(TestCase):
    """Test request workflow transitions"""

    def test_valid_transitions(self):
        """Test valid status transitions"""
        from services.request_workflow import is_valid_transition

        self.assertTrue(is_valid_transition('PENDING', 'MANAGER_APPROVED'))
        self.assertTrue(is_valid_transition('MANAGER_APPROVED', 'IT_RECEIVED'))
        self.assertTrue(is_valid_transition('IT_RECEIVED', 'IN_PROGRESS'))
        self.assertTrue(is_valid_transition('IN_PROGRESS', 'COMPLETED'))

    def test_invalid_transitions(self):
        """Test invalid status transitions"""
        from services.request_workflow import is_valid_transition

        self.assertFalse(is_valid_transition('PENDING', 'COMPLETED'))
        self.assertFalse(is_valid_transition('COMPLETED', 'PENDING'))
        self.assertFalse(is_valid_transition('PENDING', 'IN_PROGRESS'))

    def test_can_actor_transition(self):
        """Test actor permission for transitions"""
        from services.request_workflow import can_actor_transition, is_it_admin
        from accounts.models import User

        manager = User.objects.create_user(
            username='wfmanager',
            email='wfmanager@test.com',
            password='test123',
            role=User.IS_IT_ADMIN
        )
        employee = User.objects.create_user(
            username='wfemployee',
            email='wfemployee@test.com',
            password='test123',
            role=User.IS_EMPLOYEE,
            manager=manager
        )
        admin = User.objects.create_user(
            username='wfaadmin',
            email='wfaadmin@test.com',
            password='test123',
            role=User.IS_IT_ADMIN
        )

        request = Request.objects.create(
            user=employee,
            request_type='NEW',
            priority='MEDIUM',
            reason='Test',
            status='PENDING'
        )

        # Debug
        print(f'\nAdmin role: {repr(admin.role)}')
        print(f'is_it_admin(admin): {is_it_admin(admin)}')

        # Manager can approve employee's request
        result1 = can_actor_transition(manager, request, 'MANAGER_APPROVED')
        print(f'can_actor_transition(manager, request, MANAGER_APPROVED): {result1}')
        self.assertTrue(result1)

        # Employee cannot approve own request
        result2 = can_actor_transition(employee, request, 'MANAGER_APPROVED')
        print(f'can_actor_transition(employee, request, MANAGER_APPROVED): {result2}')
        self.assertFalse(result2)

        # Admin can do allowed transitions
        result3 = can_actor_transition(admin, request, 'MANAGER_APPROVED')
        print(f'can_actor_transition(admin, request, MANAGER_APPROVED): {result3}')
        self.assertTrue(result3)

        # Update request status to MANAGER_APPROVED to test next transition
        request.status = 'MANAGER_APPROVED'
        result4 = can_actor_transition(admin, request, 'IT_RECEIVED')
        print(f'can_actor_transition(admin, request, IT_RECEIVED): {result4}')
        self.assertTrue(result4)

        # Test COMPLETED from READY state
        request.status = 'READY'
        result5 = can_actor_transition(admin, request, 'COMPLETED')
        print(f'can_actor_transition(admin, request, COMPLETED): {result5}')
        self.assertTrue(result5)


class AssignmentTest(TestCase):
    """Test Assignment model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='assignuser',
            email='assign@test.com',
            password='test123',
            role=User.IS_EMPLOYEE
        )
        self.admin = User.objects.create_user(
            username='assignadmin',
            email='assignadmin@test.com',
            password='test123',
            role=User.IS_IT_ADMIN
        )
        self.category = Category.objects.create(name='Laptop')
        self.brand = Brand.objects.create(name='Dell')
        self.equipment = Equipment.objects.create(
            category=self.category,
            brand=self.brand,
            model_number='Test',
            serial_number='SN001',
            status='AVAILABLE'
        )

    def test_assignment_creation(self):
        """Test equipment assignment"""
        assignment = Assignment.objects.create(
            equipment=self.equipment,
            user=self.user,
            assigned_by=self.admin,
            notes='Test assignment'
        )

        self.assertEqual(assignment.user, self.user)
        self.assertEqual(assignment.assigned_by, self.admin)

        # Check equipment was updated
        self.equipment.refresh_from_db()
        self.assertEqual(self.equipment.status, 'ASSIGNED')


class RequestViewsTest(TestCase):
    """Test request views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='viewuser',
            email='view@test.com',
            password='test123',
            role=User.IS_EMPLOYEE
        )
        self.client.login(username='viewuser', password='test123')
        self.category = Category.objects.create(name='Laptop')

    def test_dashboard_view(self):
        """Test request dashboard"""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_create_request_view(self):
        """Test request creation view"""
        response = self.client.post(reverse('requests:create'), {
            'request_type': 'NEW',
            'priority': 'MEDIUM',
            'category_needed': self.category.id,
            'reason': 'Need a laptop',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
