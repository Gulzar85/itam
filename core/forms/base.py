# Base form widgets to avoid DRY violation
# Common Tailwind CSS classes for form widgets

import django.forms as forms

TAILWIND_INPUT = 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all'
TAILWIND_TEXTAREA = 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all'
TAILWIND_SELECT = 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all'
TAILWIND_CHECKBOX = 'w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500'
TAILWIND_DATE = 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all'
TAILWIND_NUMBER = 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all'
TAILWIND_FILE = 'w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all'


def get_text_input(placeholder=''):
    return forms.TextInput(attrs={
        'class': TAILWIND_INPUT,
        'placeholder': placeholder
    })


def get_email_input(placeholder=''):
    return forms.EmailInput(attrs={
        'class': TAILWIND_INPUT,
        'placeholder': placeholder
    })


def get_password_input(placeholder=''):
    return forms.PasswordInput(attrs={
        'class': TAILWIND_INPUT,
        'placeholder': placeholder
    })


def get_textarea(placeholder='', rows=3):
    return forms.Textarea(attrs={
        'class': TAILWIND_TEXTAREA,
        'rows': rows,
        'placeholder': placeholder
    })


def get_select(placeholder=''):
    return forms.Select(attrs={
        'class': TAILWIND_SELECT,
        'placeholder': placeholder
    })


def get_date_input():
    return forms.DateInput(attrs={
        'class': TAILWIND_DATE,
        'type': 'date'
    })


def get_number_input(placeholder='', min_val=None, max_val=None, step='1'):
    attrs = {
        'class': TAILWIND_NUMBER,
        'placeholder': placeholder,
        'step': step
    }
    if min_val is not None:
        attrs['min'] = min_val
    if max_val is not None:
        attrs['max'] = max_val
    return forms.NumberInput(attrs=attrs)


def get_file_input(accept='*/*'):
    return forms.FileInput(attrs={
        'class': TAILWIND_FILE,
        'accept': accept
    })


def get_checkbox():
    return forms.CheckboxInput(attrs={
        'class': TAILWIND_CHECKBOX
    })
