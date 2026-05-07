from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, HTML, Div, Submit
from crispy_forms.bootstrap import FormActions
from core.forms.base import (
    get_text_input, get_email_input, get_textarea, get_select,
    get_date_input, get_number_input, get_file_input, TAILWIND_INPUT
)
from core.validators import validate_image_file_extension, validate_file_size
from .models import Equipment, Vendor, Brand, Category


class EquipmentForm(forms.ModelForm):
    """Form for creating/editing equipment"""

    class Meta:
        model = Equipment
        fields = [
            'category', 'brand', 'model_number', 'serial_number',
            'original_vendor', 'current_repair_vendor', 'status',
            'purchase_date', 'purchase_cost', 'warranty_expiry', 'assigned_to', 'image'
        ]
        widgets = {
            'category': get_select('Select category'),
            'brand': get_select('Select brand'),
            'model_number': get_text_input('e.g., Latitude 5520, MacBook Pro 14"'),
            'serial_number': get_text_input('Unique serial number'),
            'original_vendor': get_select('Select vendor'),
            'current_repair_vendor': get_select('Select repair vendor'),
            'status': get_select(),
            'purchase_date': get_date_input(),
            'purchase_cost': get_number_input('0.00', min_val=0, step='0.01'),
            'warranty_expiry': get_date_input(),
            'image': forms.FileInput(attrs={
                'class': TAILWIND_INPUT,
                'accept': 'image/*'
            }),
            'assigned_to': get_select('Assign to user'),
        }
        labels = {
            'category': 'Category',
            'brand': 'Brand',
            'model_number': 'Model Number',
            'serial_number': 'Serial Number',
            'original_vendor': 'Supplier Vendor',
            'current_repair_vendor': 'Repair Vendor',
            'status': 'Status',
            'purchase_date': 'Purchase Date',
            'purchase_cost': 'Purchase Cost (PKR)',
            'warranty_expiry': 'Warranty Expiry',
            'assigned_to': 'Assigned To',
            'image': 'Equipment Image',
        }
        help_texts = {
            'serial_number': 'Unique identifier for this equipment',
            'warranty_expiry': 'When does the warranty expire?',
            'current_repair_vendor': 'Only fill if equipment is currently under repair',
            'purchase_cost': 'Original purchase price in Pakistani Rupees',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class VendorForm(forms.ModelForm):
    """Form for creating/editing vendors"""

    class Meta:
        model = Vendor
        fields = ['name', 'contact_person', 'phone', 'email', 'address', 'vendor_type', 'rating']
        widgets = {
            'name': get_text_input('Vendor company name'),
            'contact_person': get_text_input('Primary contact person name'),
            'phone': get_text_input('+1234567890'),
            'email': get_email_input('contact@vendor.com'),
            'address': get_textarea('Full vendor address', rows=3),
            'vendor_type': get_select(),
            'rating': get_number_input('', min_val=1, max_val=5, step='0.5'),
        }
        labels = {
            'name': 'Vendor Name',
            'contact_person': 'Contact Person',
            'phone': 'Phone Number',
            'email': 'Email Address',
            'address': 'Address',
            'vendor_type': 'Vendor Type',
            'rating': 'Rating (1-5)',
        }
        help_texts = {
            'vendor_type': 'Select whether this vendor supplies equipment, provides repairs, or both',
            'rating': 'Rate vendor performance from 1 to 5 stars',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class BrandForm(forms.ModelForm):
    """Form for creating/editing brands"""

    class Meta:
        model = Brand
        fields = ['name', 'support_contact', 'website']
        widgets = {
            'name': get_text_input('e.g., Dell, HP, Apple'),
            'support_contact': get_text_input('Brand helpline number'),
            'website': get_text_input('https://brand-website.com'),
        }
        labels = {
            'name': 'Brand Name',
            'support_contact': 'Support Contact',
            'website': 'Website URL',
        }
        help_texts = {
            'support_contact': 'Customer support helpline for this brand',
            'website': 'Official brand website',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class CategoryForm(forms.ModelForm):
    """Form for creating/editing categories"""

    class Meta:
        model = Category
        fields = ['name', 'icon', 'description']
        widgets = {
            'name': get_text_input('e.g., Laptop, Monitor, Printer'),
            'icon': get_text_input('e.g., laptop, monitor, printer'),
            'description': get_textarea('Category description (optional)', rows=3),
        }
        labels = {
            'name': 'Category Name',
            'icon': 'Icon Name',
            'description': 'Description',
        }
        help_texts = {
            'icon': 'Use Lucide icon names: laptop, monitor, printer, keyboard, mouse, headphones, etc.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
