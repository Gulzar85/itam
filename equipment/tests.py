"""
Comprehensive tests for equipment app
"""
import uuid
from datetime import date, timedelta
from django.test import TestCase
from django.urls import reverse
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
import io
from PIL import Image

from equipment.models import (
    Equipment, Vendor, Brand, Category, EquipmentLog, MaintenanceRecord
)
from accounts.models import Department

User = get_user_model()


class VendorModelTest(TestCase):
    """Tests for Vendor model"""

    def setUp(self):
        self.vendor = Vendor.objects.create(
            name="Test Vendor",
            contact_person="John Doe",
            phone="1234567890",
            email="vendor@test.com",
            vendor_type="SUPPLIER",
            rating=4
        )

    def test_vendor_creation(self):
        """Test vendor can be created"""
        self.assertEqual(self.vendor.name, "Test Vendor")
        self.assertEqual(self.vendor.vendor_type, "SUPPLIER")
        self.assertEqual(self.vendor.rating, 4)

    def test_vendor_str(self):
        """Test string representation"""
        self.assertEqual(str(self.vendor), "Test Vendor")

    def test_vendor_ordering(self):
        """Test vendors are ordered by name"""
        Vendor.objects.create(name="ABC Vendor", phone="111", vendor_type="SUPPLIER")
        vendors = Vendor.objects.all()
        self.assertEqual(vendors[0].name, "ABC Vendor")


class BrandModelTest(TestCase):
    """Tests for Brand model"""

    def setUp(self):
        self.brand = Brand.objects.create(
            name="Dell",
            support_contact="1-800-DELL",
            website="https://dell.com"
        )

    def test_brand_creation(self):
        """Test brand can be created"""
        self.assertEqual(self.brand.name, "Dell")
        self.assertEqual(self.brand.website, "https://dell.com")

    def test_brand_str(self):
        """Test string representation"""
        self.assertEqual(str(self.brand), "Dell")

    def test_brand_unique_name(self):
        """Test brand name must be unique"""
        with self.assertRaises(IntegrityError):
            Brand.objects.create(name="Dell")


class CategoryModelTest(TestCase):
    """Tests for Category model"""

    def setUp(self):
        self.category = Category.objects.create(
            name="Laptops",
            icon="laptop",
            description="Portable computers"
        )

    def test_category_creation(self):
        """Test category can be created"""
        self.assertEqual(self.category.name, "Laptops")
        self.assertEqual(self.category.icon, "laptop")

    def test_category_str(self):
        """Test string representation"""
        self.assertEqual(str(self.category), "Laptops")


class EquipmentModelTest(TestCase):
    """Tests for Equipment model"""

    def setUp(self):
        self.category = Category.objects.create(name="Laptops", icon="laptop")
        self.brand = Brand.objects.create(name="Dell")
        self.vendor = Vendor.objects.create(name="Dell Inc", phone="123", vendor_type="BOTH")
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123"
        )
        self.equipment = Equipment.objects.create(
            category=self.category,
            brand=self.brand,
            model_number="Latitude 5520",
            serial_number="DEL-001",
            original_vendor=self.vendor,
            status='AVAILABLE',
            purchase_date=date.today() - timedelta(days=365),
            purchase_cost=1000.00,
            warranty_expiry=date.today() + timedelta(days=365)
        )

    def test_equipment_creation(self):
        """Test equipment can be created"""
        self.assertEqual(self.equipment.serial_number, "DEL-001")
        self.assertEqual(self.equipment.status, "AVAILABLE")
        self.assertIsNotNone(self.equipment.tracking_id)

    def test_equipment_str(self):
        """Test string representation"""
        expected = "Dell Latitude 5520 - DEL-001"
        self.assertEqual(str(self.equipment), expected)

    def test_equipment_unique_serial(self):
        """Test serial number must be unique"""
        with self.assertRaises(IntegrityError):
            Equipment.objects.create(
                category=self.category,
                brand=self.brand,
                model_number="Another",
                serial_number="DEL-001"  # Duplicate
            )

    def test_generate_tracking_id(self):
        """Test tracking ID generation"""
        from services.equipment_service import EquipmentService
        tid = EquipmentService.generate_tracking_id()
        self.assertIn("EQ-", tid)
        self.assertIn(str(date.today().year), tid)

    def test_assignment_age_property(self):
        """Test assignment_age property"""
        self.equipment.assigned_to = self.user
        self.equipment.assigned_date = date.today() - timedelta(days=5)
        self.equipment.status = 'ASSIGNED'
        self.equipment.save()
        self.assertEqual(self.equipment.assignment_age, 5)

    def test_assignment_age_display(self):
        """Test assignment_age_display property"""
        # Test "today"
        self.equipment.assigned_date = date.today()
        self.equipment.status = 'ASSIGNED'
        self.assertEqual(self.equipment.assignment_age_display, "Assigned today")

        # Test days
        self.equipment.assigned_date = date.today() - timedelta(days=5)
        self.assertEqual(self.equipment.assignment_age_display, "5 days")

        # Test months
        self.equipment.assigned_date = date.today() - timedelta(days=60)
        self.assertIn("month", self.equipment.assignment_age_display)

    def test_age_in_years_property(self):
        """Test age_in_years property"""
        self.assertEqual(self.equipment.age_in_years, 1.0)

    def test_status_auto_update_on_save(self):
        """Test status auto-updates based on assigned_to"""
        self.equipment.assigned_to = self.user
        self.equipment.save()
        self.assertEqual(self.equipment.status, 'ASSIGNED')

    def test_qr_code_generation(self):
        """Test QR code is generated on save"""
        self.assertIsNotNone(self.equipment.qr_code)


class EquipmentLogModelTest(TestCase):
    """Tests for EquipmentLog model"""

    def setUp(self):
        self.category = Category.objects.create(name="Laptops", icon="laptop")
        self.brand = Brand.objects.create(name="Dell")
        self.equipment = Equipment.objects.create(
            category=self.category,
            brand=self.brand,
            model_number="Test",
            serial_number="SN-001"
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123"
        )
        self.log = EquipmentLog.objects.create(
            equipment=self.equipment,
            action_by=self.user,
            old_status="AVAILABLE",
            new_status="ASSIGNED",
            remarks="Assigned to user"
        )

    def test_log_creation(self):
        """Test log can be created"""
        self.assertEqual(self.log.old_status, "AVAILABLE")
        self.assertEqual(self.log.new_status, "ASSIGNED")

    def test_log_str(self):
        """Test string representation"""
        # The log str format is different, let's check what it actually returns
        log_str = str(self.log)
        self.assertIn(self.equipment.serial_number, log_str)


class MaintenanceRecordModelTest(TestCase):
    """Tests for MaintenanceRecord model"""

    def setUp(self):
        self.category = Category.objects.create(name="Laptops", icon="laptop")
        self.brand = Brand.objects.create(name="Dell")
        self.vendor = Vendor.objects.create(name="Repair Shop", phone="123", vendor_type="REPAIR")
        self.equipment = Equipment.objects.create(
            category=self.category,
            brand=self.brand,
            model_number="Test",
            serial_number="SN-002"
        )
        from requests.models import Request
        self.request = Request.objects.create(
            user=User.objects.create_user(username="test", email="t@t.com", password="pass"),
            request_type="REPAIR",
            reason="Broken screen"
        )
        self.record = MaintenanceRecord.objects.create(
            request=self.request,
            equipment=self.equipment,
            vendor=self.vendor,
            issue_description="Screen broken",
            estimated_cost=200.00,
            status='IN_PROGRESS'
        )

    def test_record_creation(self):
        """Test maintenance record can be created"""
        self.assertEqual(self.record.issue_description, "Screen broken")
        self.assertEqual(self.record.status, "IN_PROGRESS")

    def test_record_str(self):
        """Test string representation"""
        self.assertIn("Repair:", str(self.record))


class EquipmentViewsTest(TestCase):
    """Tests for equipment views"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="itadmin",
            email="admin@test.com",
            password="testpass123",
            role="IT_ADMIN"
        )
        self.category = Category.objects.create(name="Laptops", icon="laptop")
        self.brand = Brand.objects.create(name="Dell")
        self.vendor = Vendor.objects.create(name="Test Vendor", phone="123", vendor_type="BOTH")
        self.client.login(username='itadmin', password='testpass123')

    def test_equipment_list_view(self):
        """Test equipment list view"""
        response = self.client.get(reverse('equipment:equipment_list'))
        self.assertEqual(response.status_code, 200)

    def test_equipment_create_view(self):
        """Test equipment create view"""
        response = self.client.get(reverse('equipment:equipment_create'))
        self.assertEqual(response.status_code, 200)

    def test_vendor_list_view(self):
        """Test vendor list view"""
        response = self.client.get(reverse('equipment:vendor_list'))
        self.assertEqual(response.status_code, 200)

    def test_brand_list_view(self):
        """Test brand list view"""
        response = self.client.get(reverse('equipment:brand_list'))
        self.assertEqual(response.status_code, 200)

    def test_category_list_view(self):
        """Test category list view"""
        response = self.client.get(reverse('equipment:category_list'))
        self.assertEqual(response.status_code, 200)

    def test_non_admin_cannot_create_equipment(self):
        """Test non-admin cannot access create view"""
        self.client.logout()
        employee = User.objects.create_user(
            username="employee",
            email="emp@test.com",
            password="testpass123",
            role="EMPLOYEE"
        )
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('equipment:equipment_create'))
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_equipment_export_view(self):
        """Test equipment export to CSV"""
        response = self.client.get(reverse('equipment:equipment_export'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
