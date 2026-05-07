"""
Tests for core app
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache
from django.contrib.auth import get_user_model
from core.models import BusinessInfo, SocialMediaLink
from core.forms.forms_backup import BusinessInfoForm, SocialMediaLinkForm
import uuid

User = get_user_model()


class BusinessInfoModelTest(TestCase):
    """Test BusinessInfo model"""

    def test_business_info_creation(self):
        """Test creating business info"""
        business = BusinessInfo.objects.create(
            name='Test Company',
            description='A test company',
            address='123 Test St',
            contact_email='contact@test.com',
            contact_phone='+1234567890',
            primary_color='#DA291C',
            is_active=True
        )
        self.assertEqual(str(business), 'Test Company')
        self.assertTrue(business.is_active)

    def test_business_info_colors(self):
        """Test color fields"""
        business = BusinessInfo.objects.create(
            name='Color Test',
            primary_color='#FF0000',
            secondary_color='#00FF00',
            accent_color='#0000FF'
        )
        self.assertEqual(business.primary_color, '#FF0000')


class SocialMediaLinkModelTest(TestCase):
    """Test SocialMediaLink model"""

    def setUp(self):
        self.business = BusinessInfo.objects.create(
            name='Test Company',
            is_active=True
        )

    def test_social_media_link_creation(self):
        """Test creating social media link"""
        social = SocialMediaLink.objects.create(
            business=self.business,
            platform='facebook',
            url='https://facebook.com/testcompany'
        )
        self.assertEqual(str(social), 'facebook - Test Company')
        self.assertEqual(social.icon_class, 'fab fa-facebook')

    def test_icon_class_property(self):
        """Test icon_class property returns correct icon"""
        social = SocialMediaLink.objects.create(
            business=self.business,
            platform='twitter',
            url='https://twitter.com/test'
        )
        self.assertEqual(social.icon_class, 'fab fa-twitter')

    def test_invalid_platform_icon(self):
        """Test icon_class with invalid platform"""
        social = SocialMediaLink.objects.create(
            business=self.business,
            platform='unknown',
            url='https://example.com'
        )
        self.assertEqual(social.icon_class, 'fas fa-link')


class BusinessInfoFormTest(TestCase):
    """Test BusinessInfoForm"""

    def test_form_valid_data(self):
        """Test form with valid data"""
        form_data = {
            'name': 'New Company',
            'description': 'Company description',
            'address': '123 Main St',
            'contact_email': 'info@company.com',
            'contact_phone': '+1234567890',
            'website': 'https://company.com',
            'primary_color': '#DA291C',
            'secondary_color': '#FFC72C',
            'accent_color': '#FFBD0A',
            'is_active': True
        }
        form = BusinessInfoForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_email(self):
        """Test form with invalid email"""
        form_data = {
            'name': 'Test',
            'contact_email': 'invalid-email',
        }
        form = BusinessInfoForm(data=form_data)
        self.assertFalse(form.is_valid())


class SocialMediaLinkFormTest(TestCase):
    """Test SocialMediaLinkForm"""

    def setUp(self):
        self.business = BusinessInfo.objects.create(
            name='Test',
            is_active=True
        )

    def test_form_valid_data(self):
        """Test form with valid data"""
        form_data = {
            'platform': 'linkedin',
            'url': 'https://linkedin.com/company/test'
        }
        form = SocialMediaLinkForm(data=form_data)
        self.assertTrue(form.is_valid())


class ContextProcessorTest(TestCase):
    """Test context processors"""

    def setUp(self):
        self.business = BusinessInfo.objects.create(
            name='Test Company',
            is_active=True,
            primary_color='#DA291C'
        )
        self.user = User.objects.create_user(
            username='testcontext',
            email='context@test.com',
            password='test123',
            role=User.IS_EMPLOYEE
        )

    def test_business_context(self):
        """Test business_context processor"""
        from core.context_processors import business_context
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user

        context = business_context(request)
        self.assertEqual(context['business_info'], self.business)
        self.assertEqual(context['theme_colors']['primary'], '#DA291C')

    def test_business_context_caching(self):
        """Test that business info is cached"""
        cache.clear()
        from core.context_processors import get_cached_business_info

        # First call - should hit DB
        business1 = get_cached_business_info()
        # Second call - should hit cache
        business2 = get_cached_business_info()

        self.assertEqual(business1, business2)
        # Verify cache is set
        cached = cache.get('business_info_active')
        self.assertIsNotNone(cached)


class SequenceCounterTest(TestCase):
    """Test SequenceCounter model"""

    def test_get_next_value(self):
        """Test atomic counter increment"""
        from core.models import SequenceCounter

        # First call
        val1 = SequenceCounter.get_next_value('TEST', 2026)
        self.assertEqual(val1, 1)

        # Second call
        val2 = SequenceCounter.get_next_value('TEST', 2026)
        self.assertEqual(val2, 2)

        # Different prefix
        val3 = SequenceCounter.get_next_value('OTHER', 2026)
        self.assertEqual(val3, 1)

    def test_year_reset(self):
        """Test counter resets when year changes"""
        from core.models import SequenceCounter

        val1 = SequenceCounter.get_next_value('RESET', 2025)
        val2 = SequenceCounter.get_next_value('RESET', 2026)

        self.assertEqual(val1, 1)
        self.assertEqual(val2, 1)  # Reset for new year


class ViewTest(TestCase):
    """Test core views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testview',
            email='view@test.com',
            password='testpass123',
            role=User.IS_EMPLOYEE
        )
        self.client.login(username='testview', password='testpass123')

    def test_global_search_no_query(self):
        """Test global search with no query"""
        response = self.client.get('/api/search/', {'q': ''})
        self.assertEqual(response.status_code, 200)
        import json
        data = json.loads(response.content)
        self.assertEqual(data['results'], [])

    def test_global_search_short_query(self):
        """Test global search with query too short"""
        response = self.client.get('/api/search/', {'q': 'a'})
        self.assertEqual(response.status_code, 200)
        import json
        data = json.loads(response.content)
        self.assertEqual(data['results'], [])
