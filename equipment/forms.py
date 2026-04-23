from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, HTML, Div, Submit
from crispy_forms.bootstrap import FormActions
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
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'placeholder': 'Select category'
            }),
            'brand': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'placeholder': 'Select brand'
            }),
            'model_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'placeholder': 'e.g., Latitude 5520, MacBook Pro 14"'
            }),
            'serial_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'placeholder': 'Unique serial number'
            }),
            'original_vendor': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'placeholder': 'Select vendor'
            }),
            'current_repair_vendor': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'placeholder': 'Select repair vendor'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all'
            }),
            'purchase_date': forms.DateInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'type': 'date'
            }),
            'purchase_cost': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'placeholder': '0.00',
                'min': '0',
                'step': '0.01'
            }),
            'warranty_expiry': forms.DateInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'type': 'date'
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'accept': 'image/*'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'placeholder': 'Assign to user'
            }),
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
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'placeholder': 'Vendor company name'
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'placeholder': 'Primary contact person name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'placeholder': '+1234567890'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'placeholder': 'contact@vendor.com'
            }),
            'address': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'rows': 3,
                'placeholder': 'Full vendor address'
            }),
            'vendor_type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all'
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'min': 1,
                'max': 5,
                'step': 0.5
            }),
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
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'placeholder': 'e.g., Dell, HP, Apple'
            }),
            'support_contact': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'placeholder': 'Brand helpline number'
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'placeholder': 'https://brand-website.com'
            }),
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
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'placeholder': 'e.g., Laptop, Monitor, Printer'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'placeholder': 'e.g., laptop, monitor, printer'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'rows': 3,
                'placeholder': 'Category description (optional)'
            }),
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
