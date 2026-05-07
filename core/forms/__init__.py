from .base import (
    get_text_input, get_email_input, get_textarea, get_select,
    get_date_input, get_number_input, get_file_input, get_checkbox,
    TAILWIND_INPUT, TAILWIND_TEXTAREA, TAILWIND_SELECT,
    TAILWIND_CHECKBOX, TAILWIND_DATE, TAILWIND_NUMBER, TAILWIND_FILE
)
from .base import get_password_input

# Lazy import - forms are imported where needed to avoid circular imports
# Import directly from core.forms.forms_backup where needed


