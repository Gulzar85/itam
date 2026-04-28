import uuid
from django.utils import timezone

from django.conf import settings
from django.db import models, transaction

from core.models import SequenceCounter

from equipment.models import Brand, Category, Equipment, Vendor


class Request(models.Model):
    REQUEST_TYPE_CHOICES = [
        ('NEW', 'New Equipment Procurement'),
        ('REPAIR', 'Repair Existing Equipment'),
    ]

    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending Manager Approval'),
        ('MANAGER_APPROVED', 'Approved by Manager'),
        ('IT_RECEIVED', 'Received by IT'),
        ('IN_PROGRESS', 'In Progress / With Vendor'),
        ('READY', 'Ready for Collection'),
        ('COMPLETED', 'Completed & Closed'),
        ('REJECTED', 'Rejected'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request_id = models.CharField(max_length=20, unique=True, editable=False, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Who is requesting?
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='my_requests')

    # Request Details
    request_type = models.CharField(
        max_length=10, choices=REQUEST_TYPE_CHOICES)
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='PENDING')

    # Specifics
    # Agar Repair hai, to maujooda equipment link hoga
    equipment = models.ForeignKey(
        Equipment, on_delete=models.SET_NULL, null=True, blank=True)

    # Agar New Request hai, to category aur brand preference
    category_needed = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True)
    brand_preference = models.ForeignKey(
        Brand, on_delete=models.SET_NULL, null=True, blank=True)

    reason = models.TextField(help_text="Zaroorat ya maslay ki tafseel")

    # IT Admin Assignment (Kis vendor ko diya gaya)
    assigned_vendor = models.ForeignKey(
        Vendor, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['status', 'user']),
            models.Index(fields=['created_at']),
            models.Index(fields=['request_id']),
        ]

    def __str__(self):
        return f"REQ#{self.request_id} - {self.user.username} ({self.request_type})" if self.request_id else f"REQ#{self.id} - {self.user.username} ({self.request_type})"

    def generate_request_id(self):
        year = timezone.now().year
        prefix = 'REQ'
        next_value = SequenceCounter.get_next_value(prefix, year)
        return f"{prefix}-{year}-{str(next_value).zfill(4)}"

    def save(self, *args, **kwargs):
        if not self.request_id:
            self.request_id = self.generate_request_id()
        super().save(*args, **kwargs)


class RequestLog(models.Model):
    request = models.ForeignKey(
        Request, on_delete=models.CASCADE, related_name='logs')
    action_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    remarks = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log for REQ#{self.request.id} by {self.action_by}"


class Assignment(models.Model):
    equipment = models.ForeignKey(
        Equipment, on_delete=models.CASCADE, related_name='assignments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    assigned_date = models.DateField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='processed_assignments'
    )
    returned_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'returned_date']),
        ]

    def __str__(self):
        return f"{self.equipment} -> {self.user}"
