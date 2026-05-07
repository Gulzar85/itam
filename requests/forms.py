from django import forms
from crispy_forms.helper import FormHelper
from core.forms.base import get_select, get_textarea, get_text_input
from .models import Request
from equipment.models import Equipment


class ITRequestForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = ['request_type', 'priority', 'category_needed', 'brand_preference', 'equipment', 'reason']
        widgets = {
            'request_type': get_select(),
            'priority': get_select(),
            'category_needed': get_select(),
            'brand_preference': get_select(),
            'equipment': get_select(),
            'reason': get_textarea('Please provide details about your request...', rows=4),
        }
        labels = {
            'request_type': 'Request Type',
            'priority': 'Priority Level',
            'category_needed': 'Required Category',
            'brand_preference': 'Brand Preference',
            'equipment': 'Equipment (for Repair)',
            'reason': 'Reason / Description',
        }
        help_texts = {
            'request_type': 'NEW: Request new equipment | REPAIR: Repair existing equipment',
            'priority': 'CRITICAL: Urgent | HIGH: Important | MEDIUM: Normal | LOW: Can wait',
            'category_needed': 'Select the category of equipment you need',
            'brand_preference': 'Any specific brand preference? (optional)',
            'equipment': 'Select the specific equipment that needs repair',
            'reason': 'Explain why you need this equipment or what issues you are facing',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        equipment_field = self.fields.get('equipment')
        if isinstance(equipment_field, forms.ModelChoiceField):
            if user:
                equipment_field.queryset = Equipment.objects.filter(
                    assigned_to=user,
                    status__in=['ASSIGNED', 'REPAIRING']
                ).select_related('category', 'brand')
            else:
                equipment_field.queryset = Equipment.objects.filter(
                    status='ASSIGNED'
                ).select_related('category', 'brand')

        self.fields['equipment'].required = False
        self.fields['category_needed'].required = False
        self.fields['brand_preference'].required = False

    def clean(self):
        cleaned_data = super().clean()
        request_type = cleaned_data.get('request_type')
        equipment = cleaned_data.get('equipment')
        category = cleaned_data.get('category_needed')

        if request_type == 'REPAIR' and not equipment:
            self.add_error('equipment', 'Please select the equipment that needs repair.')

        if request_type == 'NEW' and not category:
            self.add_error('category_needed', 'Please select a category for your request.')

        return cleaned_data
