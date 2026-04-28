from django.db import models, transaction
from django.conf import settings
from decimal import Decimal
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image
from accounts.models import User
from django.utils import timezone
from core.models import SequenceCounter


class Vendor(models.Model):
    VENDOR_TYPE = [
        ('SUPPLIER', 'Equipment Supplier'),
        ('REPAIR', 'Repair Service Provider'),
        ('BOTH', 'Both Supplier & Repair'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    vendor_type = models.CharField(
        max_length=20, choices=VENDOR_TYPE, default='BOTH')

    # Track performance
    rating = models.IntegerField(default=5, help_text="Rating out of 5")

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Brand(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    support_contact = models.CharField(
        max_length=100, blank=True, help_text="Brand helpline number")
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, help_text="Tailwind/Heroicons name")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Equipment(models.Model):
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('ASSIGNED', 'Assigned'),
        ('REPAIRING', 'Under Repair'),
        ('DAMAGED', 'Damaged/Retired'),
    ]
    tracking_id = models.CharField(max_length=20, unique=True, editable=False)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='equipments')
    brand = models.ForeignKey(
        Brand, on_delete=models.PROTECT, related_name='equipments')
    model_number = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100, unique=True)

    # Vendor Links
    # Jis vendor se khareeda gaya
    original_vendor = models.ForeignKey(
        Vendor,
        on_delete=models.SET_NULL,
        null=True,
        related_name='supplied_items'
    )

    # Current repair vendor (agar repair per hai)
    current_repair_vendor = models.ForeignKey(
        Vendor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='repairing_items'
    )

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')

    # Track who equipment is assigned to
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_equipment'
    )

    purchase_date = models.DateField(null=True, blank=True)
    purchase_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Purchase price in PKR")
    warranty_expiry = models.DateField(null=True, blank=True)
    assigned_date = models.DateField(null=True, blank=True, help_text="Date when equipment was assigned")

    image = models.ImageField(
        upload_to='equipment_pics/', null=True, blank=True)

    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['status', 'assigned_to']),
            models.Index(fields=['purchase_date']),
            models.Index(fields=['tracking_id']),
        ]

    def generate_tracking_id(self):
        """
        Generates a custom ID like EQ-2026-0001 using atomic counter
        """
        year = timezone.now().year
        prefix = 'EQ'
        next_value = SequenceCounter.get_next_value(prefix, year)
        return f"{prefix}-{year}-{str(next_value).zfill(4)}"

    def save(self, *args, **kwargs):
        # 1. Generate Tracking ID (only on first creation) - wrapped in atomic transaction
        if not self.tracking_id:
            self.tracking_id = self.generate_tracking_id()

        if self.assigned_to and self.status == 'AVAILABLE':
            self.status = 'ASSIGNED'
        elif self.status == 'ASSIGNED' and not self.assigned_to:
            self.status = 'AVAILABLE'
        elif self.status == 'REPAIRING' and not self.current_repair_vendor:
            self.status = 'ASSIGNED' if self.assigned_to else 'AVAILABLE'

        # --- QR Code Logic ---
        if not self.qr_code:
            qr_content = f"EQ:{self.tracking_id}\nSN:{self.serial_number}\nModel:{self.model_number}"

            # 1. Setup QR with better formatting
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,  # Size of each individual box
                border=4,    # Standard white border (Quiet Zone)
            )

            qr.add_data(qr_content)
            qr.make(fit=True)

            # 2. Generate the image directly from the qr object
            # This handles the canvas and padding automatically
            img = qr.make_image(fill_color="black", back_color="white")

            # 3. Save to buffer
            buffer = BytesIO()
            img.save(buffer, 'PNG')

            filename = f'qr-{self.tracking_id}.png'
            self.qr_code.save(filename, File(buffer), save=False)

        super().save(*args, **kwargs)

    @property
    def assignment_age(self):
        """Returns days since equipment was assigned"""
        if self.assigned_date and self.status == 'ASSIGNED':
            return (timezone.now().date() - self.assigned_date).days
        return None

    @property
    def assignment_age_display(self):
        """Returns human-readable assignment age"""
        days = self.assignment_age
        if days is None:
            return None
        if days == 0:
            return "Assigned today"
        elif days == 1:
            return "1 day"
        elif days < 30:
            return f"{days} days"
        elif days < 365:
            months = days // 30
            return f"{months} month{'s' if months > 1 else ''}"
        else:
            years = days // 365
            return f"{years} year{'s' if years > 1 else ''}"
    
    @property
    def age_in_years(self):
        """Returns how old the equipment is since purchase"""
        if self.purchase_date:
            days = (timezone.now().date() - self.purchase_date).days
            return round(days / 365.25, 1)
        return None

    def __str__(self):
        return f"{self.brand} {self.model_number} - {self.serial_number}"


class EquipmentLog(models.Model):
    equipment = models.ForeignKey(
        Equipment, on_delete=models.CASCADE, related_name='logs')
    action_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    remarks = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.equipment} - {self.old_status} to {self.new_status} by {self.action_by} on {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class MaintenanceRecord(models.Model):
    request = models.OneToOneField(
        'requests.Request', on_delete=models.CASCADE, related_name='maintenance_detail')
    equipment = models.ForeignKey(
        'equipment.Equipment', on_delete=models.CASCADE)
    vendor = models.ForeignKey(
        Vendor, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    issue_description = models.TextField()
    estimated_cost = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'))
    actual_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)

    sent_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField(null=True, blank=True)
    actual_return_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('IN_PROGRESS', 'In Progress'), ('COMPLETED', 'Completed')],
        default='IN_PROGRESS'
    )

    repair_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Repair: {self.equipment.serial_number} at {self.vendor.name if self.vendor else 'TBD'}"
