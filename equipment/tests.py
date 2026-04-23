import uuid
from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from accounts.models import Department, User
from equipment.models import Brand, Category, Equipment, EquipmentLog, Vendor


class VendorModelTest(TestCase):
    def test_vendor_creation(self):
        vendor = Vendor.objects.create(
            name="Test Vendor",
            phone="+1234567890",
            email="test@vendor.com",
            vendor_type="BOTH",
            rating=4,
        )
        self.assertEqual(str(vendor), "Test Vendor")
        self.assertEqual(vendor.rating, 4)

    def test_vendor_choices(self):
        for vendor_type, label in Vendor.VENDOR_TYPE:
            vendor = Vendor.objects.create(
                name=f"Vendor {vendor_type}",
                phone="+1234567890",
                vendor_type=vendor_type,
            )
            self.assertEqual(vendor.vendor_type, vendor_type)


class BrandModelTest(TestCase):
    def test_brand_unique_name(self):
        Brand.objects.create(name="Dell", support_contact="+1234567890")
        with self.assertRaises(Exception):
            Brand.objects.create(name="Dell")

    def test_brand_str(self):
        brand = Brand.objects.create(name="HP")
        self.assertEqual(str(brand), "HP")


class CategoryModelTest(TestCase):
    def test_category_creation(self):
        category = Category.objects.create(name="Desktop", icon="monitor")
        self.assertEqual(str(category), "Desktop")


class EquipmentModelTest(TestCase):
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
        cls.vendor = Vendor.objects.create(
            name="Test Vendor",
            phone="+1234567890",
            vendor_type="SUPPLIER",
        )
        cls.category = Category.objects.create(name="Laptop", icon="laptop")
        cls.brand = Brand.objects.create(name="Dell")

    def test_equipment_creation(self):
        equipment = Equipment.objects.create(
            category=self.category,
            brand=self.brand,
            model_number="Latitude 5420",
            serial_number="DELL001",
            original_vendor=self.vendor,
            status="AVAILABLE",
            purchase_date=date.today(),
            warranty_expiry=date.today() + timedelta(days=365),
        )
        self.assertTrue(equipment.tracking_id.startswith("EQ-"))
        self.assertEqual(equipment.status, "AVAILABLE")

    def test_tracking_id_unique(self):
        eq1 = Equipment.objects.create(
            category=self.category,
            brand=self.brand,
            model_number="Model 1",
            serial_number="SN001",
            status="AVAILABLE",
        )
        eq2 = Equipment.objects.create(
            category=self.category,
            brand=self.brand,
            model_number="Model 2",
            serial_number="SN002",
            status="AVAILABLE",
        )
        self.assertNotEqual(eq1.tracking_id, eq2.tracking_id)

    def test_equipment_status_assignment(self):
        equipment = Equipment.objects.create(
            category=self.category,
            brand=self.brand,
            model_number="Test",
            serial_number="TEST001",
            status="AVAILABLE",
        )
        equipment.assigned_to = self.user
        equipment.save()
        self.assertEqual(equipment.status, "ASSIGNED")

    def test_equipment_str(self):
        equipment = Equipment.objects.create(
            category=self.category,
            brand=self.brand,
            model_number="XPS 15",
            serial_number="XPS001",
            status="AVAILABLE",
        )
        self.assertIn("XPS 15", str(equipment))
        self.assertIn("XPS001", str(equipment))

    def test_uuid_primary_key(self):
        equipment = Equipment.objects.create(
            category=self.category,
            brand=self.brand,
            model_number="Test",
            serial_number="UUID001",
            status="AVAILABLE",
        )
        self.assertIsInstance(equipment.id, uuid.UUID)


class EquipmentLogModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.department = Department.objects.create(name="IT")
        cls.user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="pass123",
            role=User.IS_IT_ADMIN,
            department=cls.department,
            is_staff=True,
        )
        cls.category = Category.objects.create(name="Laptop", icon="laptop")
        cls.brand = Brand.objects.create(name="Dell")
        cls.equipment = Equipment.objects.create(
            category=cls.category,
            brand=cls.brand,
            model_number="Test",
            serial_number="LOG001",
            status="AVAILABLE",
        )

    def test_equipment_log_creation(self):
        log = EquipmentLog.objects.create(
            equipment=self.equipment,
            action_by=self.user,
            old_status="AVAILABLE",
            new_status="ASSIGNED",
            remarks="Assigned to employee",
        )
        self.assertEqual(log.old_status, "AVAILABLE")
        self.assertEqual(log.new_status, "ASSIGNED")


class EquipmentViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.department = Department.objects.create(name="IT")
        cls.it_admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="admin123",
            role=User.IS_IT_ADMIN,
            department=cls.department,
            is_staff=True,
        )
        cls.employee = User.objects.create_user(
            username="employee",
            email="employee@example.com",
            password="employee123",
            role=User.IS_EMPLOYEE,
            department=cls.department,
        )
        cls.category = Category.objects.create(name="Laptop", icon="laptop")
        cls.brand = Brand.objects.create(name="Dell")
        cls.vendor = Vendor.objects.create(
            name="Vendor", phone="+1234567890", vendor_type="SUPPLIER"
        )

    def test_equipment_list_requires_login(self):
        response = self.client.get(reverse("equipment:equipment_list"))
        self.assertEqual(response.status_code, 302)

    def test_equipment_list_for_authenticated(self):
        self.client.login(username="employee", password="employee123")
        response = self.client.get(reverse("equipment:equipment_list"))
        self.assertEqual(response.status_code, 200)

    def test_vendor_list_accessible_by_authenticated(self):
        self.client.login(username="employee", password="employee123")
        response = self.client.get(reverse("equipment:vendor_list"))
        self.assertEqual(response.status_code, 200)

    def test_vendor_list_accessible_by_admin(self):
        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse("equipment:vendor_list"))
        self.assertEqual(response.status_code, 200)
