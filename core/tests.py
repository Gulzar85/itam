from django.test import TestCase
from django.urls import reverse
from core.models import BusinessInfo, SocialMediaLink


class BusinessInfoModelTest(TestCase):
    def test_business_info_creation(self):
        business = BusinessInfo.objects.create(
            name="Test Company",
            description="A test company",
            address="123 Test Street",
            contact_email="info@testcompany.com",
            contact_phone="+1234567890",
            website="https://testcompany.com",
            primary_color="#2563eb",
            is_active=True,
        )
        self.assertEqual(str(business), "Test Company")
        self.assertTrue(business.is_active)

    def test_business_info_unique_name(self):
        BusinessInfo.objects.create(name="Unique Company", contact_email="a@test.com", contact_phone="+1234567890")
        with self.assertRaises(Exception):
            BusinessInfo.objects.create(name="Unique Company", contact_email="b@test.com", contact_phone="+1234567891")

    def test_business_info_unique_email(self):
        BusinessInfo.objects.create(name="Company 1", contact_email="unique@test.com", contact_phone="+1234567890")
        with self.assertRaises(Exception):
            BusinessInfo.objects.create(name="Company 2", contact_email="unique@test.com", contact_phone="+1234567891")


class SocialMediaLinkModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.business = BusinessInfo.objects.create(
            name="Test Corp",
            description="Test description",
            address="123 Street",
            contact_email="test@testcorp.com",
            contact_phone="+1234567890",
        )

    def test_social_media_link_creation(self):
        link = SocialMediaLink.objects.create(
            business=self.business,
            platform="facebook",
            url="https://facebook.com/testcorp",
        )
        self.assertEqual(str(link), "facebook - Test Corp")

    def test_social_media_icon_class(self):
        link = SocialMediaLink.objects.create(
            business=self.business,
            platform="linkedin",
            url="https://linkedin.com/testcorp",
        )
        self.assertIn("fab fa-linkedin", link.icon_class)

    def test_social_media_icon_map(self):
        link = SocialMediaLink.objects.create(
            business=self.business,
            platform="twitter",
            url="https://twitter.com/test",
        )
        self.assertIn("fab fa-twitter", link.icon_class)


class BusinessInfoViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.business = BusinessInfo.objects.create(
            name="Test Corp",
            description="Test description",
            address="123 Street",
            contact_email="test@testcorp.com",
            contact_phone="+1234567890",
            primary_color="#2563eb",
        )

    def test_business_info_view_requires_login(self):
        response = self.client.get(reverse("core:business_info"))
        self.assertEqual(response.status_code, 302)