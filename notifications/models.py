from django.db import models
from django.conf import settings
import uuid


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('REQUEST_CREATED', 'New Request Created'),
        ('REQUEST_APPROVED', 'Request Approved'),
        ('REQUEST_REJECTED', 'Request Rejected'),
        ('REQUEST_COMPLETED', 'Request Completed'),
        ('EQUIPMENT_ASSIGNED', 'Equipment Assigned'),
        ('EQUIPMENT_RETURNED', 'Equipment Returned'),
        ('MAINTENANCE_DUE', 'Maintenance Due'),
        ('WARRANTY_EXPIRING', 'Warranty Expiring'),
        ('SYSTEM_ALERT', 'System Alert'),
        ('ACTION_PERFORMED', 'Action Performed'),
    ]

    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='MEDIUM'
    )

    # Related objects (optional)
    related_request = models.ForeignKey(
        'requests.Request',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    related_equipment = models.ForeignKey(
        'equipment.Equipment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Status
    is_read = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)

    # Timestamps
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['notification_type', 'created_at']),
        ]

    def __str__(self):
        return f"{self.notification_type} - {self.recipient.username}"

    def mark_as_read(self):
        """Mark notification as read"""
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    @property
    def is_overdue(self):
        """Check if high priority notification is unread for more than 24 hours"""
        from django.utils import timezone
        if self.priority in ['HIGH', 'CRITICAL'] and not self.is_read:
            return (timezone.now() - self.created_at).total_seconds() > 86400  # 24 hours
        return False


class NotificationTemplate(models.Model):
    """Templates for different types of notifications"""
    notification_type = models.CharField(
        max_length=20,
        choices=Notification.NOTIFICATION_TYPES,
        unique=True
    )
    subject_template = models.CharField(max_length=200)
    message_template = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Template for {self.notification_type}"
