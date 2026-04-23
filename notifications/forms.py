from django import forms
from crispy_forms.helper import FormHelper
from .models import NotificationTemplate


class NotificationTemplateForm(forms.ModelForm):
    """Form for creating/editing notification templates"""

    class Meta:
        model = NotificationTemplate
        fields = ['notification_type', 'subject_template', 'message_template', 'is_active']
        widgets = {
            'notification_type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all'
            }),
            'subject_template': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'placeholder': 'e.g., Request #{{request_id}} - Status Update'
            }),
            'message_template': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all',
                'rows': 6,
                'placeholder': 'e.g., Dear {{user_name}}, your request #{{request_id}} has been {{status}}.'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
        }
        labels = {
            'notification_type': 'Notification Type',
            'subject_template': 'Email Subject',
            'message_template': 'Message Template',
            'is_active': 'Active',
        }
        help_texts = {
            'subject_template': 'Subject line for email notifications. Use {{placeholder}} for dynamic values.',
            'message_template': 'Message body. Available placeholders: {{user_name}}, {{request_id}}, {{request_type}}, {{status}}, {{manager_name}}, {{equipment_name}}, {{serial_number}}, {{expiry_date}}, {{alert_message}}',
            'is_active': 'Enable this template for notifications',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
