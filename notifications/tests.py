import uuid
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Department, User
from core.models import BusinessInfo
from equipment.models import Category, Brand, Equipment
from notifications.models import Notification, NotificationTemplate
from requests.models import Request


class NotificationModelTest(TestCase):
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

    def test_notification_creation(self):
        notification = Notification.objects.create(
            recipient=self.user,
            notification_type="REQUEST_CREATED",
            title="New Request",
            message="You have a new request",
            priority="MEDIUM",
        )
        self.assertEqual(str(notification), f"REQUEST_CREATED - {self.user.username}")
        self.assertFalse(notification.is_read)

    def test_notification_mark_as_read(self):
        notification = Notification.objects.create(
            recipient=self.user,
            notification_type="REQUEST_CREATED",
            title="New Request",
            message="You have a new request",
            priority="HIGH",
        )
        notification.mark_as_read()
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)

    def test_notification_is_overdue_property(self):
        notification = Notification.objects.create(
            recipient=self.user,
            notification_type="SYSTEM_ALERT",
            title="Low Alert",
            message="Low priority alert",
            priority="LOW",
            is_read=False,
        )
        self.assertFalse(notification.is_overdue)

    def test_notification_choices(self):
        for notif_type, label in Notification.NOTIFICATION_TYPES:
            notification = Notification.objects.create(
                recipient=self.user,
                notification_type=notif_type,
                title=f"Test {label}",
                message="Test message",
            )
            self.assertEqual(notification.notification_type, notif_type)

    def test_notification_priority_choices(self):
        for priority in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
            notification = Notification.objects.create(
                recipient=self.user,
                notification_type="SYSTEM_ALERT",
                title="Test",
                message="Test",
                priority=priority,
            )
            self.assertEqual(notification.priority, priority)


class NotificationTemplateModelTest(TestCase):
    def test_notification_template_creation(self):
        template = NotificationTemplate.objects.create(
            notification_type="REQUEST_CREATED",
            subject_template="New Request - #{{request_id}}",
            message_template="Request created by {{user_name}}",
            is_active=True,
        )
        self.assertEqual(str(template), "Template for REQUEST_CREATED")

    def test_notification_template_unique_type(self):
        NotificationTemplate.objects.create(
            notification_type="REQUEST_CREATED",
            subject_template="Subject",
            message_template="Message",
        )
        with self.assertRaises(Exception):
            NotificationTemplate.objects.create(
                notification_type="REQUEST_CREATED",
                subject_template="Another Subject",
                message_template="Another Message",
            )


class NotificationViewsTest(TestCase):
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

    def test_notification_list_requires_login(self):
        response = self.client.get(reverse("notifications:list"))
        self.assertEqual(response.status_code, 302)

    def test_notification_list_for_authenticated(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("notifications:list"))
        self.assertEqual(response.status_code, 200)

    def test_notification_list_filters_unread(self):
        Notification.objects.create(
            recipient=self.user,
            notification_type="REQUEST_CREATED",
            title="Unread",
            message="Test",
            is_read=False,
        )
        Notification.objects.create(
            recipient=self.user,
            notification_type="REQUEST_APPROVED",
            title="Read",
            message="Test",
            is_read=True,
        )
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("notifications:list"))
        self.assertEqual(response.context["unread_count"], 1)

    def test_mark_as_read_view(self):
        notif = Notification.objects.create(
            recipient=self.user,
            notification_type="REQUEST_CREATED",
            title="Test",
            message="Test",
            is_read=False,
        )
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(reverse("notifications:mark_read", kwargs={"pk": notif.pk}))
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)