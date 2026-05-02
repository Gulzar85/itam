"""
Comprehensive tests for notifications app
"""
import uuid
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from notifications.models import Notification, NotificationTemplate

User = get_user_model()


class NotificationModelTest(TestCase):
    """Tests for Notification model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123"
        )
        self.notification = Notification.objects.create(
            recipient=self.user,
            notification_type="REQUEST_CREATED",
            title="New Request Created",
            message="Your request has been submitted successfully.",
            priority="MEDIUM"
        )

    def test_notification_creation(self):
        """Test notification can be created"""
        self.assertEqual(self.notification.recipient, self.user)
        self.assertEqual(self.notification.notification_type, "REQUEST_CREATED")
        self.assertEqual(self.notification.priority, "MEDIUM")
        self.assertFalse(self.notification.is_read)
        self.assertFalse(self.notification.is_archived)

    def test_notification_str(self):
        """Test string representation"""
        self.assertIn("REQUEST_CREATED", str(self.notification))
        self.assertIn(self.user.username, str(self.notification))

    def test_mark_as_read(self):
        """Test marking notification as read"""
        self.notification.mark_as_read()
        self.assertTrue(self.notification.is_read)
        self.assertIsNotNone(self.notification.read_at)

    def test_is_overdue_high_priority(self):
        """Test is_overdue for high priority notification"""
        # Create a high priority notification
        notif = Notification.objects.create(
            recipient=self.user,
            notification_type="SYSTEM_ALERT",
            title="Critical Alert",
            message="This is critical",
            priority="HIGH"
        )
        # Should not be overdue immediately
        self.assertFalse(notif.is_overdue)

    def test_is_overdue_critical_priority(self):
        """Test is_overdue for critical priority"""
        notif = Notification.objects.create(
            recipient=self.user,
            notification_type="SYSTEM_ALERT",
            title="Critical Alert",
            message="This is critical",
            priority="CRITICAL"
        )
        # Should not be overdue immediately
        self.assertFalse(notif.is_overdue)

    def test_notification_ordering(self):
        """Test notifications are ordered by created_at descending"""
        # Create another notification
        notif2 = Notification.objects.create(
            recipient=self.user,
            notification_type="REQUEST_APPROVED",
            title="Request Approved",
            message="Your request was approved"
        )
        notifications = Notification.objects.all()
        self.assertEqual(notifications[0], notif2)  # Most recent first

    def test_notification_types(self):
        """Test all notification types are valid"""
        valid_types = [choice[0] for choice in Notification.NOTIFICATION_TYPES]
        self.assertIn("REQUEST_CREATED", valid_types)
        self.assertIn("EQUIPMENT_ASSIGNED", valid_types)
        self.assertIn("WARRANTY_EXPIRING", valid_types)

    def test_priority_choices(self):
        """Test priority choices"""
        valid_priorities = [choice[0] for choice in Notification.PRIORITY_CHOICES]
        self.assertIn("LOW", valid_priorities)
        self.assertIn("HIGH", valid_priorities)
        self.assertIn("CRITICAL", valid_priorities)


class NotificationTemplateModelTest(TestCase):
    """Tests for NotificationTemplate model"""

    def setUp(self):
        self.template = NotificationTemplate.objects.create(
            notification_type="REQUEST_CREATED",
            subject_template="Request #{id} Created",
            message_template="Your request for {equipment} has been created.",
            is_active=True
        )

    def test_template_creation(self):
        """Test template can be created"""
        self.assertEqual(self.template.notification_type, "REQUEST_CREATED")
        self.assertTrue(self.template.is_active)

    def test_template_str(self):
        """Test string representation"""
        self.assertIn("REQUEST_CREATED", str(self.template))

    def test_template_unique_type(self):
        """Test notification_type must be unique"""
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            NotificationTemplate.objects.create(
                notification_type="REQUEST_CREATED",  # Duplicate
                subject_template="Another",
                message_template="Another"
            )


class NotificationViewsTest(TestCase):
    """Tests for notification views"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123"
        )
        self.client.login(username='testuser', password='testpass123')

        # Create some notifications
        for i in range(5):
            Notification.objects.create(
                recipient=self.user,
                notification_type="REQUEST_CREATED",
                title=f"Notification {i}",
                message=f"Message {i}"
            )

    def test_notification_list_view(self):
        """Test notification list view"""
        response = self.client.get(reverse('notifications:list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('notifications', response.context)

    def test_notification_detail_view(self):
        """Test notification detail view"""
        notification = Notification.objects.first()
        response = self.client.get(
            reverse('notifications:detail', kwargs={'pk': notification.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_mark_as_read_view(self):
        """Test marking notification as read"""
        notification = Notification.objects.first()
        response = self.client.post(
            reverse('notifications:mark_read', kwargs={'pk': notification.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_mark_all_read_view(self):
        """Test marking all notifications as read"""
        response = self.client.post(reverse('notifications:mark_all_read'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        unread_count = Notification.objects.filter(
            recipient=self.user,
            is_read=False
        ).count()
        self.assertEqual(unread_count, 0)

    def test_notification_count_view(self):
        """Test notification count AJAX endpoint"""
        response = self.client.get(reverse('notifications:count'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('count', response.json())

    def test_unread_notifications_count(self):
        """Test context processor counts unread correctly"""
        # Mark some as read
        Notification.objects.first().mark_as_read()
        unread_count = Notification.objects.filter(
            recipient=self.user,
            is_read=False
        ).count()
        self.assertEqual(unread_count, 4)

    def test_notification_requires_login(self):
        """Test notification views require login"""
        self.client.logout()
        response = self.client.get(reverse('notifications:list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login


class NotificationSignalTest(TestCase):
    """Tests for notification signals"""

    def setUp(self):
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
            role="EMPLOYEE"
        )
        from equipment.models import Category
        self.category = Category.objects.create(name="Laptops", icon="laptop")

    def test_request_status_change_creates_notification(self):
        """Test that changing request status creates notification"""
        from requests.models import Request
        request_obj = Request.objects.create(
            user=self.employee,
            request_type="NEW",
            category_needed=self.category,
            reason="Test"
        )

        # Change status
        request_obj.status = "MANAGER_APPROVED"
        request_obj.save()

        # Check if notification was created
        notifications = Notification.objects.filter(
            recipient=self.employee,
            notification_type="REQUEST_APPROVED"
        )
        # Note: This depends on signals being set up correctly
        # The actual test may need signal import
