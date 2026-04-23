from django import forms
from crispy_forms.helper import FormHelper
from .models import BusinessInfo, SocialMediaLink


class BusinessInfoForm(forms.ModelForm):
    """Form for editing business information"""

    class Meta:
        model = BusinessInfo
        fields = [
            'name', 'logo', 'description', 'address', 'contact_email',
            'contact_phone', 'website', 'primary_color', 'secondary_color', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'placeholder': 'Company/Organization Name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'rows': 4,
                'placeholder': 'Brief description of your organization'
            }),
            'address': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'rows': 3,
                'placeholder': 'Full address'
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'placeholder': 'contact@company.com'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'placeholder': '+1234567890'
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'placeholder': 'https://company-website.com'
            }),
            'primary_color': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'type': 'color'
            }),
            'secondary_color': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'type': 'color'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
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
            'is_active': 'Active',
        }
        help_texts = {
            'logo': 'Upload a logo image (max 2MB). Recommended size: 200x200px',
            'primary_color': 'Main brand color for buttons and accents',
            'secondary_color': 'Background color for the application',
            'is_active': 'Enable to show this business info publicly',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class SocialMediaLinkForm(forms.ModelForm):
    """Form for creating/editing social media links"""

    class Meta:
        model = SocialMediaLink
        fields = ['platform', 'url']
        widgets = {
            'platform': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all'
            }),
            'url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'placeholder': 'https://platform.com/yourcompany'
            }),
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
