"""
Tests for equipment app
"""
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from equipment.models import Equipment, Brand, Category, Vendor, EquipmentLog, MaintenanceRecord
from accounts.models import User, Department
import uuid
from datetime import date, timedelta
from django.utils import timezone


class BrandModelTest(TestCase):
    """Test Brand model"""

    def test_brand_creation(self):
        brand = Brand.objects.create(name='Dell')
        self.assertEqual(str(brand), 'Dell')
        self.assertEqual(brand.name, 'Dell')

    def test_brand_unique_name(self):
        """Test brand name uniqueness"""
        Brand.objects.create(name='HP')
        with self.assertRaises(Exception):
            Brand.objects.create(name='HP')


class CategoryModelTest(TestCase):
    """Test Category model"""

    def test_category_creation(self):
        category = Category.objects.create(
            name='Laptop',
            icon='laptop',
            description='Portable computers'
        )
        self.assertEqual(str(category), 'Laptop')
        self.assertEqual(category.icon, 'laptop')


class VendorModelTest(TestCase):
    """Test Vendor model"""

    def test_vendor_creation(self):
        vendor = Vendor.objects.create(
            name='Tech Supplies Inc',
            contact_person='John Doe',
            phone='+1234567890',
            vendor_type='SUPPLIER'
        )
        self.assertEqual(str(vendor), 'Tech Supplies Inc')
        self.assertEqual(vendor.rating, 5)  # Default rating

    def test_vendor_type_choices(self):
        """Test vendor type choices"""
        vendor = Vendor.objects.create(
            name='Repair Shop',
            vendor_type='REPAIR'
        )
        self.assertEqual(vendor.vendor_type, 'REPAIR')


class EquipmentModelTest(TestCase):
    """Test Equipment model"""

    def setUp(self):
        self.category = Category.objects.create(name='Laptop')
        self.brand = Brand.objects.create(name='Dell')
        self.vendor = Vendor.objects.create(name='Dell Inc')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='test123'
        )

    def test_equipment_creation(self):
        """Test equipment creation"""
        equipment = Equipment.objects.create(
            category=self.category,
            brand=self.brand,
            model_number='Latitude 5520',
            serial_number='DELL001',
            original_vendor=self.vendor,
            status='AVAILABLE'
        )
        self.assertEqual(equipment.model_number, 'Latitude 5520')
        self.assertEqual(equipment.status, 'AVAILABLE')
        self.assertIsNotNone(equipment.tracking_id)
        self.assertTrue(equipment.tracking_id.startswith('EQ-'))

    def test_equipment_assignment(self):
        """Test equipment assignment to user"""
        equipment = Equipment.objects.create(
            category=self.category,
            brand=self.brand,
            model_number='Test Model',
            serial_number='SN001',
            status='AVAILABLE'
        )

        equipment.assigned_to = self.user
        equipment.status = 'ASSIGNED'
        equipment.assigned_date = date.today()
        equipment.save()

        self.assertEqual(equipment.assigned_to, self.user)
        self.assertEqual(equipment.status, 'ASSIGNED')

    def test_assignment_age_property(self):
        """Test assignment_age property"""
        equipment = Equipment.objects.create(
            category=self.category,
            brand=self.brand,
            model_number='Test',
            serial_number='SN002',
            assigned_to=self.user,
            status='ASSIGNED',
            assigned_date=date.today() - timedelta(days=5)
        )
        self.assertEqual(equipment.assignment_age, 5)

    def test_age_in_years_property(self):
        """Test age_in_years property"""
        equipment = Equipment.objects.create(
            category=self.category,
            brand=self.brand,
            model_number='Test',
            serial_number='SN003',
            purchase_date=date.today() - timedelta(days=365)
        )
        self.assertAlmostEqual(equipment.age_in_years, 1.0, places=1)


class EquipmentFormTest(TestCase):
    """Test EquipmentForm"""

    def setUp(self):
        self.category = Category.objects.create(name='Laptop')
        self.brand = Brand.objects.create(name='Dell')
        self.vendor = Vendor.objects.create(name='Test Vendor')

    def test_form_valid_data(self):
        from equipment.forms import EquipmentForm
        form_data = {
            'category': self.category.id,
            'brand': self.brand.id,
            'model_number': 'Latitude 5520',
            'serial_number': 'DELL001',
            'original_vendor': self.vendor.id,
            'status': 'AVAILABLE',
            'purchase_cost': '1000.00',
        }
        form = EquipmentForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_serial_number(self):
        """Test duplicate serial number validation"""
        Equipment.objects.create(
            category=self.category,
            brand=self.brand,
            model_number='Test',
            serial_number='DUPLICATE'
        )
        from equipment.forms import EquipmentForm
        form_data = {
            'category': self.category.id,
            'brand': self.brand.id,
            'model_number': 'Test2',
            'serial_number': 'DUPLICATE',  # Duplicate
            'status': 'AVAILABLE',
        }
        form = EquipmentForm(data=form_data)
        self.assertFalse(form.is_valid())


class EquipmentServiceTest(TestCase):
    """Test EquipmentService"""

    def setUp(self):
        self.category = Category.objects.create(name='Laptop')
        self.brand = Brand.objects.create(name='Dell')
        self.user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='admin123',
            role='IT_ADMIN'
        )

    def test_generate_tracking_id(self):
        """Test tracking ID generation"""
        from services.equipment_service import EquipmentService
        tracking_id = EquipmentService.generate_tracking_id()
        self.assertTrue(tracking_id.startswith('EQ-'))
        self.assertIn(str(timezone.now().year), tracking_id)

    def test_update_equipment_status(self):
        """Test status update with logging"""
        equipment = Equipment.objects.create(
            category=self.category,
            brand=self.brand,
            model_number='Test',
            serial_number='SN001',
            status='AVAILABLE'
        )

        from services.equipment_service import EquipmentService
        EquipmentService.update_equipment_status(
            equipment=equipment,
            new_status='DAMAGED',
            action_by=self.user,
            remarks='Test damage'
        )

        equipment.refresh_from_db()
        self.assertEqual(equipment.status, 'DAMAGED')

        # Check log was created
        log = EquipmentLog.objects.filter(equipment=equipment).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.old_status, 'AVAILABLE')
        self.assertEqual(log.new_status, 'DAMAGED')


class EquipmentViewsTest(TestCase):
    """Test equipment views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='equipmenttest',
            email='equipment@test.com',
            password='testpass123',
            role=User.IS_IT_ADMIN
        )
        self.client.login(username='equipmenttest', password='testpass123')
        self.category = Category.objects.create(name='Laptop')
        self.brand = Brand.objects.create(name='Dell')
        self.vendor = Vendor.objects.create(
            name='Test Vendor',
            vendor_type='SUPPLIER'
        )

    def test_equipment_list_view(self):
        """Test equipment list view"""
        response = self.client.get(reverse('equipment:equipment_list'))
        self.assertEqual(response.status_code, 200)

    def test_equipment_create_view(self):
        """Test equipment creation"""
        response = self.client.post(reverse('equipment:equipment_create'), {
            'category': self.category.id,
            'brand': self.brand.id,
            'model_number': 'New Model',
            'serial_number': 'NEW001',
            'status': 'AVAILABLE',
            'original_vendor': self.vendor.id,
        })
        # Check if form is valid
        if response.status_code == 200:
            # Form has errors, print them
            print("Form errors:", response.context['form'].errors if 'form' in response.context else 'No form in context')
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(Equipment.objects.filter(serial_number='NEW001').exists())


class FileUploadValidationTest(TestCase):
    """Test file upload validation"""

    def test_validate_image_extension(self):
        """Test image extension validator"""
        from core.validators import validate_image_file_extension
        from django.core.exceptions import ValidationError

        # Valid file
        valid_file = SimpleUploadedFile(
            "test.jpg", b"file_content", content_type="image/jpeg"
        )
        try:
            validate_image_file_extension(valid_file)
        except ValidationError:
            self.fail("validate_image_file_extension raised ValidationError unexpectedly!")

    def test_validate_file_size(self):
        """Test file size validator"""
        from core.validators import validate_file_size
        from django.core.exceptions import ValidationError

        # Create a file larger than 2MB
        large_file = SimpleUploadedFile(
            "large.jpg", b"x" * (3 * 1024 * 1024), content_type="image/jpeg"
        )
        with self.assertRaises(ValidationError):
            validate_file_size(large_file)
