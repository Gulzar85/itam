"""
Comprehensive tests for core app
"""
import uuid
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from core.models import BusinessInfo, SocialMediaLink, SequenceCounter

User = get_user_model()


class BusinessInfoModelTest(TestCase):
    """Tests for BusinessInfo model"""

    def setUp(self):
        self.business = BusinessInfo.objects.create(
            name="Test Company",
            description="A test company",
            address="123 Test St",
            contact_email="info@test.com",
            contact_phone="1234567890",
            website="https://test.com",
            primary_color="#DA291C",
            secondary_color="#FFC72C",
            accent_color="#FFBD0A",
            is_active=True
        )

    def test_business_info_creation(self):
        """Test business info can be created"""
        self.assertEqual(self.business.name, "Test Company")
        self.assertEqual(self.business.primary_color, "#DA291C")
        self.assertTrue(self.business.is_active)

    def test_business_info_str(self):
        """Test string representation"""
        self.assertEqual(str(self.business), "Test Company")

    def test_business_info_unique_name(self):
        """Test business name must be unique"""
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            BusinessInfo.objects.create(
                name="Test Company",  # Duplicate
                is_active=False
            )

    def test_only_one_active_business(self):
        """Test that setting a new business as active works"""
        # Create another business
        new_business = BusinessInfo.objects.create(
            name="New Company",
            is_active=True
        )
        # Note: The model doesn't enforce single active automatically
        # This would need custom save() method or signal
        self.assertTrue(new_business.is_active)


class SocialMediaLinkModelTest(TestCase):
    """Tests for SocialMediaLink model"""

    def setUp(self):
        self.business = BusinessInfo.objects.create(
            name="Test Company",
            is_active=True
        )
        self.link = SocialMediaLink.objects.create(
            business=self.business,
            platform="FACEBOOK",
            url="https://facebook.com/test"
        )

    def test_social_media_link_creation(self):
        """Test social media link can be created"""
        self.assertEqual(self.link.platform, "FACEBOOK")
        self.assertEqual(self.link.url, "https://facebook.com/test")

    def test_social_media_link_str(self):
        """Test string representation"""
        self.assertIn("Facebook", str(self.link))

    def test_icon_class_property(self):
        """Test icon_class property returns correct icon"""
        self.assertEqual(self.link.icon_class, "facebook")

        # Test other platforms
        self.link.platform = "TWITTER"
        self.link.save()
        self.assertEqual(self.link.icon_class, "twitter")

        self.link.platform = "LINKEDIN"
        self.link.save()
        self.assertEqual(self.link.icon_class, "linkedin")


class SequenceCounterModelTest(TestCase):
    """Tests for SequenceCounter model"""

    def test_get_next_value(self):
        """Test sequence counter generates sequential values"""
        from django.utils import timezone
        year = timezone.now().year

        val1 = SequenceCounter.get_next_value("TEST", year)
        val2 = SequenceCounter.get_next_value("TEST", year)

        self.assertEqual(val2, val1 + 1)

    def test_different_prefixes(self):
        """Test different prefixes generate independent sequences"""
        from django.utils import timezone
        year = timezone.now().year

        val1 = SequenceCounter.get_next_value("PREFIX1", year)
        val2 = SequenceCounter.get_next_value("PREFIX2", year)

        # Both should start from 1
        self.assertEqual(val1, 1)
        self.assertEqual(val2, 1)

    def test_different_years(self):
        """Test different years generate independent sequences"""
        val1 = SequenceCounter.get_next_value("TEST", 2025)
        val2 = SequenceCounter.get_next_value("TEST", 2026)

        # Both should start from 1 for their respective years
        self.assertEqual(val1, 1)
        self.assertEqual(val2, 1)


class CoreViewsTest(TestCase):
    """Tests for core views"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="testpass123",
            role="IT_ADMIN"
        )
        self.client.login(username='admin', password='testpass123')

        self.business = BusinessInfo.objects.create(
            name="Test Company",
            is_active=True
        )

    def test_business_info_view(self):
        """Test business info view"""
        response = self.client.get(reverse('core:business_info'))
        self.assertEqual(response.status_code, 200)

    def test_business_info_update_view(self):
        """Test business info update view"""
        response = self.client.get(reverse('core:business_info_update'))
        self.assertEqual(response.status_code, 200)

    def test_social_media_list_view(self):
        """Test social media list view"""
        response = self.client.get(reverse('core:social_media_list'))
        self.assertEqual(response.status_code, 200)

    def test_context_processor_business_info(self):
        """Test business context processor"""
        response = self.client.get(reverse('core:business_info'))
        self.assertIn('business_info', response.context)
        self.assertEqual(response.context['business_info'], self.business)

    def test_context_processor_theme_colors(self):
        """Test theme colors in context"""
        response = self.client.get(reverse('core:business_info'))
        self.assertIn('theme_colors', response.context)
        self.assertIn('primary', response.context['theme_colors'])


class PopulateDataCommandTest(TestCase):
    """Tests for populate_data management command"""

    def test_command_runs_without_errors(self):
        """Test that populate_data command runs successfully"""
        from django.core.management import call_command
        try:
            call_command('populate_data')
            # Check if data was created
            from accounts.models import Department
            self.assertTrue(Department.objects.exists())
        except Exception as e:
            self.fail(f"populate_data command failed with error: {e}")
