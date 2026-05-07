from django import forms
from crispy_forms.helper import FormHelper
from core.forms.base import (
    get_text_input, get_email_input, get_textarea, get_select,
    get_date_input, get_number_input, get_file_input, get_checkbox, TAILWIND_INPUT
)
from core.validators import validate_image_file_extension, validate_file_size
from core.models import BusinessInfo, SocialMediaLink


class BusinessInfoForm(forms.ModelForm):
    """Form for editing business information"""

    class Meta:
        model = BusinessInfo
        fields = [
            'name', 'logo', 'description', 'address', 'contact_email',
            'contact_phone', 'website', 'primary_color', 'secondary_color', 'accent_color', 'is_active'
        ]
        widgets = {
            'name': get_text_input('Company/Organization Name'),
            'description': get_textarea('Brief description of your organization', rows=4),
            'address': get_textarea('Full address', rows=3),
            'contact_email': get_email_input('contact@company.com'),
            'contact_phone': get_text_input('+1234567890'),
            'website': get_text_input('https://company-website.com'),
            'primary_color': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'type': 'color'
            }),
            'secondary_color': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'type': 'color'
            }),
            'accent_color': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'type': 'color'
            }),
            'is_active': get_checkbox(),
            'logo': forms.FileInput(attrs={
                'class': TAILWIND_INPUT,
                'accept': 'image/*'
            }),
        }
        labels = {
            'name': 'Company Name',
            'logo': 'Company Logo',
            'description': 'Description',
            'address': 'Address',
            'contact_email': 'Contact Email',
            'contact_phone': 'Contact Phone',
            'website': 'Website',
            'primary_color': 'Primary Color',
            'secondary_color': 'Secondary Color',
            'accent_color': 'Accent Color',
            'is_active': 'Active',
        }
        help_texts = {
            'logo': 'Upload a logo image (max 2MB). Recommended size: 200x200px',
            'primary_color': 'Main brand color (McDonald\'s Red: #DA291C)',
            'secondary_color': 'Background color (McDonald\'s Yellow: #FFC72C)',
            'accent_color': 'Highlight color for badges and accents',
            'is_active': 'Enable to show this business info publicly',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

    def clean_logo(self):
        """Validate logo file"""
        logo = self.cleaned_data.get('logo')
        if logo:
            validate_image_file_extension(logo)
            validate_file_size(logo)
        return logo


class SocialMediaLinkForm(forms.ModelForm):
    """Form for creating/editing social media links"""

    class Meta:
        model = SocialMediaLink
        fields = ['platform', 'url']
        widgets = {
            'platform': get_select(),
            'url': get_text_input('https://platform.com/yourcompany'),
        }
        labels = {
            'platform': 'Social Platform',
            'url': 'Profile URL',
        }
        help_texts = {
            'url': 'Full URL to your social media profile or page',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
