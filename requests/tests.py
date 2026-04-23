import uuid
from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Department, User
from equipment.models import Brand, Category, Equipment, Vendor
from requests.models import Assignment, Request, RequestLog


class RequestModelTest(TestCase):
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
        cls.category = Category.objects.create(name="Laptop", icon="laptop")
        cls.brand = Brand.objects.create(name="Dell")
        cls.vendor = Vendor.objects.create(
            name="Test Vendor",
            phone="+1234567890",
            vendor_type="BOTH",
        )

    def test_request_creation(self):
        req = Request.objects.create(
            user=self.user,
            request_type="NEW",
            priority="HIGH",
            category_needed=self.category,
            brand_preference=self.brand,
            reason="Need a new laptop for work",
        )
        self.assertEqual(str(req.user), f"{self.user.username} ({self.user.role})")
        self.assertEqual(req.status, "PENDING")
        self.assertEqual(req.priority, "HIGH")

    def test_request_uuid_unique(self):
        req1 = Request.objects.create(
            user=self.user, request_type="NEW", reason="Test 1"
        )
        req2 = Request.objects.create(
            user=self.user, request_type="NEW", reason="Test 2"
        )
        self.assertNotEqual(req1.id, req2.id)
        self.assertIsInstance(req1.id, uuid.UUID)

    def test_request_status_choices(self):
        req = Request.objects.create(
            user=self.user, request_type="NEW", reason="Test"
        )
        for status_code, status_name in Request.STATUS_CHOICES:
            req.status = status_code
            req.save()
            req.refresh_from_db()
            self.assertEqual(req.status, status_code)

    def test_requestlog_creation(self):
        req = Request.objects.create(
            user=self.user, request_type="NEW", reason="Test"
        )
        log = RequestLog.objects.create(
            request=req,
            action_by=self.user,
            old_status="PENDING",
            new_status="MANAGER_APPROVED",
            remarks="Approved by manager",
        )
        self.assertEqual(log.request, req)
        self.assertEqual(log.old_status, "PENDING")
        self.assertEqual(log.new_status, "MANAGER_APPROVED")


class RequestViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.department = Department.objects.create(name="IT")
        cls.manager = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="manager123",
            role=User.IS_MANAGER,
            department=cls.department,
        )
        cls.employee = User.objects.create_user(
            username="employee",
            email="employee@example.com",
            password="employee123",
            role=User.IS_EMPLOYEE,
            department=cls.department,
            manager=cls.manager,
        )
        cls.it_admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="admin123",
            role=User.IS_IT_ADMIN,
            department=cls.department,
            is_staff=True,
        )
        cls.category = Category.objects.create(name="Laptop", icon="laptop")
        cls.brand = Brand.objects.create(name="Dell")

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_allowed_for_authenticated(self):
        self.client.login(username="employee", password="employee123")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_employee_sees_own_requests(self):
        Request.objects.create(
            user=self.employee, request_type="NEW", reason="My request"
        )
        self.client.login(username="employee", password="employee123")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Request.objects.filter(user=self.employee, reason="My request").exists())

    def test_manager_sees_team_requests(self):
        Request.objects.create(
            user=self.employee, request_type="NEW", reason="Team request"
        )
        self.client.login(username="manager", password="manager123")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Request.objects.filter(user=self.employee, reason="Team request").exists())

    def test_it_admin_sees_all_requests(self):
        Request.objects.create(
            user=self.employee, request_type="NEW", reason="Admin request"
        )
        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Request.objects.filter(reason="Admin request").exists())

    def test_request_create_view(self):
        self.client.login(username="employee", password="employee123")
        response = self.client.post(
            reverse("requests:create"),
            {
                "request_type": "NEW",
                "priority": "MEDIUM",
                "category_needed": self.category.id,
                "brand_preference": self.brand.id,
                "reason": "Need new equipment",
            },
        )
        self.assertTrue(
            Request.objects.filter(reason="Need new equipment").exists()
        )

    def test_manager_approval_permission(self):
        req = Request.objects.create(
            user=self.employee,
            request_type="NEW",
            reason="Test",
            status="PENDING",
        )
        self.client.login(username="manager", password="manager123")
        response = self.client.post(
            reverse("requests:update_action", kwargs={"pk": req.pk}),
            {"status": "MANAGER_APPROVED", "remarks": "Approved"},
        )
        self.assertEqual(response.status_code, 200)
        req.refresh_from_db()
        self.assertEqual(req.status, "MANAGER_APPROVED")

    def test_unauthorized_cannot_approve(self):
        new_employee = User.objects.create_user(
            username="other_employee",
            email="other@example.com",
            password="pass123",
            role=User.IS_EMPLOYEE,
            department=self.department,
        )
        req = Request.objects.create(
            user=self.employee,
            request_type="NEW",
            reason="Test",
            status="PENDING",
        )
        self.client.login(username="other_employee", password="pass123")
        response = self.client.post(
            reverse("requests:update_action", kwargs={"pk": req.pk}),
            {"status": "MANAGER_APPROVED", "remarks": "Approved"},
        )
        self.assertEqual(response.status_code, 403)


class AssignmentModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.department = Department.objects.create(name="IT")
        cls.user = User.objects.create_user(
            username="assign_user",
            email="assign@example.com",
            password="pass123",
            role=User.IS_EMPLOYEE,
            department=cls.department,
        )
        cls.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="pass123",
            role=User.IS_IT_ADMIN,
            department=cls.department,
            is_staff=True,
        )
        cls.category = Category.objects.create(name="Laptop", icon="laptop")
        cls.brand = Brand.objects.create(name="Apple")
        cls.vendor = Vendor.objects.create(
            name="Vendor", phone="+1234567890", vendor_type="SUPPLIER"
        )

    def test_assignment_creation(self):
        equipment = Equipment.objects.create(
            category=self.category,
            brand=self.brand,
            model_number="MacBook Pro",
            serial_number="MPB001",
            status="AVAILABLE",
        )
        assignment = Assignment.objects.create(
            equipment=equipment,
            user=self.user,
            assigned_by=self.admin,
            notes="Assigned for project work",
        )
        self.assertEqual(assignment.equipment, equipment)
        self.assertEqual(assignment.user, self.user)
        self.assertIsNone(assignment.returned_date)
