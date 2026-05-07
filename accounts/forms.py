from django import forms
from crispy_forms.helper import FormHelper
from django.contrib.auth.forms import UserChangeForm
from accounts.models import User
from core.forms.base import (
    get_text_input, get_email_input, get_select, TAILWIND_TEXTAREA
)


class UserProfileForm(forms.ModelForm):
    """Form for users to edit their own profile information."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'department', 'manager']
        widgets = {
            'first_name': get_text_input('Your first name'),
            'last_name': get_text_input('Your last name'),
            'email': get_email_input('your.email@company.com'),
            'phone_number': get_text_input('+1234567890'),
            'department': get_select(),
            'manager': get_select(),
        }
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email Address',
            'phone_number': 'Phone Number',
            'department': 'Department',
            'manager': 'Line Manager',
        }
        help_texts = {
            'first_name': 'Your given name',
            'last_name': 'Your family name',
            'email': 'Your email address for notifications',
            'phone_number': 'Contact number with country code (e.g., +923123456789)',
            'department': 'Your department within the organization',
            'manager': 'Your direct reporting manager',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.fields['email'].required = True
        self.fields['department'].required = False
        self.fields['manager'].required = False
        self.fields['phone_number'].required = False


from core.forms.base import get_password_input

class UserCreationForm(forms.ModelForm):
    """Form for creating new users (admin only)"""

    password1 = forms.CharField(
        label='Password',
        widget=get_password_input('Enter password')
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=get_password_input('Confirm password')
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'department', 'manager', 'phone_number']
        widgets = {
            'username': get_text_input('Username'),
            'email': get_email_input('email@company.com'),
            'first_name': get_text_input('First name'),
            'last_name': get_text_input('Last name'),
            'role': get_select(),
            'department': get_select(),
            'manager': get_select(),
            'phone_number': get_text_input('+1234567890'),
        }
        labels = {
            'username': 'Username',
            'email': 'Email Address',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'role': 'User Role',
            'department': 'Department',
            'manager': 'Line Manager',
            'phone_number': 'Phone Number',
        }
        help_texts = {
            'role': 'EMPLOYEE: Regular staff | IT_ADMIN: System administrator',
            'manager': 'Select the user who will approve this employee\'s requests',
            'phone_number': 'Contact number (optional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.fields['department'].required = False
        self.fields['manager'].required = False
        self.fields['phone_number'].required = False

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match')
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user
