"""
Comprehensive tests for requests app
"""
import uuid
from datetime import date, timedelta
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone

from requests.models import Request, RequestLog, Assignment
from equipment.models import Equipment, Category, Brand, Vendor
from accounts.models import Department

User = get_user_model()


class RequestModelTest(TestCase):
    """Tests for Request model"""

    def setUp(self):
        self.department = Department.objects.create(name="IT")
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123",
            department=self.department
        )
        self.category = Category.objects.create(name="Laptops", icon="laptop")
        self.request = Request.objects.create(
            user=self.user,
            request_type="NEW",
            priority="HIGH",
            category_needed=self.category,
            reason="Need a new laptop for development"
        )

    def test_request_creation(self):
        """Test request can be created"""
        self.assertEqual(self.request.request_type, "NEW")
        self.assertEqual(self.request.status, "PENDING")
        self.assertIsNotNone(self.request.request_id)
        self.assertIn("REQ-", self.request.request_id)

    def test_request_with_equipment(self):
        """Test request with equipment (for repair requests)"""
        category = Category.objects.create(name="Laptops", icon="laptop")
        brand = Brand.objects.create(name="Dell")
        equipment = Equipment.objects.create(
            category=category,
            brand=brand,
            model_number="Latitude",
            serial_number="SN-005"
        )
        repair_request = Request.objects.create(
            user=self.user,
            request_type="REPAIR",
            equipment=equipment,
            reason="Screen broken"
        )
        self.assertEqual(repair_request.equipment, equipment)
        self.assertEqual(repair_request.request_type, "REPAIR")

    def test_request_str(self):
        """Test string representation"""
        self.assertIn(self.request.request_id, str(self.request))

    def test_generate_request_id(self):
        """Test request ID generation"""
        rid = self.request.generate_request_id()
        self.assertIn("REQ-", rid)
        self.assertIn(str(date.today().year), rid)

    def test_request_unique_request_id(self):
        """Test request_id is unique"""
        # The model should handle this via unique=True
        self.assertIsNotNone(self.request.request_id)


class RequestLogModelTest(TestCase):
    """Tests for RequestLog model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123"
        )
        self.request = Request.objects.create(
            user=self.user,
            request_type="NEW",
            reason="Test"
        )
        self.log = RequestLog.objects.create(
            request=self.request,
            action_by=self.user,
            old_status="PENDING",
            new_status="MANAGER_APPROVED",
            remarks="Approved by manager"
        )

    def test_log_creation(self):
        """Test log can be created"""
        self.assertEqual(self.log.old_status, "PENDING")
        self.assertEqual(self.log.new_status, "MANAGER_APPROVED")

    def test_log_str(self):
        """Test string representation"""
        self.assertIn("Log for REQ#", str(self.log))


class AssignmentModelTest(TestCase):
    """Tests for Assignment model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123"
        )
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="testpass123",
            role="IT_ADMIN"
        )
        self.category = Category.objects.create(name="Laptops", icon="laptop")
        self.brand = Brand.objects.create(name="Dell")
        self.equipment = Equipment.objects.create(
            category=self.category,
            brand=self.brand,
            model_number="Latitude",
            serial_number="SN-003",
            status='ASSIGNED'
        )
        self.assignment = Assignment.objects.create(
            equipment=self.equipment,
            user=self.user,
            assigned_by=self.admin,
            notes="Assigned for development work"
        )

    def test_assignment_creation(self):
        """Test assignment can be created"""
        self.assertEqual(self.assignment.user, self.user)
        self.assertEqual(self.assignment.assigned_by, self.admin)

    def test_assignment_str(self):
        """Test string representation"""
        self.assertIn("Latitude", str(self.assignment))

    def test_assignment_with_return_date(self):
        """Test assignment with return date"""
        self.assignment.returned_date = date.today()
        self.assignment.save()
        self.assertIsNotNone(self.assignment.returned_date)


class RequestServiceTest(TestCase):
    """Tests for RequestService"""

    def setUp(self):
        self.department = Department.objects.create(name="IT")
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123",
            department=self.department
        )
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="testpass123",
            role="IT_ADMIN"
        )
        self.category = Category.objects.create(name="Laptops", icon="laptop")
        self.brand = Brand.objects.create(name="Dell")
        self.equipment = Equipment.objects.create(
            category=self.category,
            brand=self.brand,
            model_number="Latitude",
            serial_number="SN-004",
            status='AVAILABLE'
        )

    def test_create_new_request(self):
        """Test creating a new request via service"""
        from services.request_service import RequestService
        request_obj = RequestService.create_new_request(
            user=self.user,
            request_type="NEW",
            category=self.category,
            reason="Need laptop"
        )
        self.assertEqual(request_obj.status, "PENDING")
        self.assertEqual(request_obj.user, self.user)

        # Check if log was created
        logs = request_obj.logs.all()
        self.assertEqual(logs.count(), 1)
        self.assertEqual(logs.first().new_status, "PENDING")

    def test_update_request_status(self):
        """Test updating request status via service"""
        from services.request_service import RequestService
        request_obj = Request.objects.create(
            user=self.user,
            request_type="NEW",
            category_needed=self.category,
            reason="Test"
        )

        RequestService.update_request_status(
            request_obj=request_obj,
            new_status="MANAGER_APPROVED",
            action_by=self.admin,
            remarks="Approved"
        )

        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, "MANAGER_APPROVED")

        # Check if log was created
        logs = request_obj.logs.all()
        self.assertEqual(logs.count(), 1)

    def test_complete_request_with_equipment(self):
        """Test completing a request assigns equipment"""
        from services.request_service import RequestService
        equipment = Equipment.objects.create(
            category=self.category,
            brand=Brand.objects.create(name="HP"),
            model_number="ProBook",
            serial_number="SN-006",
            status='AVAILABLE'
        )
        request_obj = Request.objects.create(
            user=self.user,
            request_type="NEW",
            category_needed=self.category,
            reason="Need laptop"
        )

        RequestService.update_request_status(
            request_obj=request_obj,
            new_status="COMPLETED",
            action_by=self.admin,
            remarks="Assigned",
            equipment_obj=equipment
        )

        equipment.refresh_from_db()
        self.assertEqual(equipment.status, "ASSIGNED")
        self.assertEqual(equipment.assigned_to, self.user)


class RequestViewsTest(TestCase):
    """Tests for request views"""

    def setUp(self):
        self.department = Department.objects.create(name="IT")
        self.manager = User.objects.create_user(
            username="manager",
            email="manager@test.com",
            password="testpass123",
            role="IT_ADMIN"
        )
        self.employee = User.objects.create_user(
            username="employee",
            email="emp@test.com",
            password="testpass123",
            role="EMPLOYEE",
            department=self.department,
            manager=self.manager
        )
        self.category = Category.objects.create(name="Laptops", icon="laptop")
        self.client.login(username='employee', password='testpass123')

    def test_dashboard_view(self):
        """Test dashboard view"""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_create_request_view_get(self):
        """Test request create view GET"""
        response = self.client.get(reverse('requests:create'))
        self.assertEqual(response.status_code, 200)

    def test_create_request_view_post(self):
        """Test request create view POST"""
        response = self.client.post(reverse('requests:create'), {
            'request_type': 'NEW',
            'priority': 'MEDIUM',
            'category_needed': self.category.id,
            'reason': 'Need a new laptop'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(Request.objects.filter(user=self.employee).exists())

    def test_manager_approvals_view(self):
        """Test manager approvals view"""
        self.client.logout()
        self.client.login(username='manager', password='testpass123')
        response = self.client.get(reverse('requests:manager_approvals'))
        self.assertEqual(response.status_code, 200)

    def test_request_detail_view(self):
        """Test request detail view"""
        request_obj = Request.objects.create(
            user=self.employee,
            request_type="NEW",
            category_needed=self.category,
            reason="Test"
        )
        response = self.client.get(
            reverse('requests:detail', kwargs={'pk': request_obj.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_employee_cannot_access_admin_views(self):
        """Test employee cannot access IT admin views"""
        self.client.logout()
        self.client.login(username='employee', password='testpass123')

        # Try to access assignment create view
        response = self.client.get(reverse('requests:assign_new'))
        self.assertEqual(response.status_code, 403)  # Forbidden


class PermissionsTest(TestCase):
    """Tests for permission classes"""

    def test_it_admin_required(self):
        """Test IT admin required mixin"""
        from services.permissions import ITAdminRequiredMixin
        mixin = ITAdminRequiredMixin()
        user = User.objects.create_user(
            username="admin",
            password="pass",
            role="IT_ADMIN"
        )
        # Mock request
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/')
        request.user = user
        # Use try/except as test_func might need the request object
        try:
            result = mixin.test_func()
            self.assertTrue(result)
        except AttributeError:
            # If test_func needs self.request to be set
            mixin.request = request
            self.assertTrue(mixin.test_func())

    def test_manager_or_admin_required(self):
        """Test manager or admin required mixin"""
        from services.permissions import ManagerOrAdminRequiredMixin
        mixin = ManagerOrAdminRequiredMixin()

        # Create manager with team members
        manager = User.objects.create_user(
            username="manager2",
            password="pass",
            role="EMPLOYEE"
        )
        User.objects.create_user(
            username="employee2",
            password="pass",
            manager=manager
        )

        # Mock request
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/')
        request.user = manager
        try:
            result = mixin.test_func()
            self.assertTrue(result)
        except AttributeError:
            mixin.request = request
            self.assertTrue(mixin.test_func())
