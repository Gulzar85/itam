"""
Custom validators for file uploads and security
"""
import os
from django.core.exceptions import ValidationError
from django.conf import settings


def validate_image_file_extension(value):
    """
    Validate that uploaded file has allowed image extension
    Usage in forms: 
        FileField(validators=[validate_image_file_extension])
    """
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = getattr(settings, 'VALID_IMAGE_EXTENSIONS', ['.jpg', '.jpeg', '.png', '.gif', '.bmp'])
    
    if ext not in valid_extensions:
        raise ValidationError(
            f'Unsupported file extension. Allowed: {", ".join(valid_extensions)}'
        )
    
    return value


def validate_file_size(value):
    """
    Validate file size doesn't exceed maximum
    Usage in forms:
        FileField(validators=[validate_file_size])
    """
    max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 2 * 1024 * 1024)  # Default 2MB
    
    if value.size > max_size:
        max_mb = max_size / (1024 * 1024)
        raise ValidationError(f'File size must be under {max_mb}MB')
    
    return value


def validate_image_content_type(value):
    """
    Validate MIME type of uploaded image
    Note: This requires reading file content, use with caution
    """
    valid_mime_types = getattr(settings, 'VALID_IMAGE_MIME_TYPES', [
        'image/jpeg', 'image/png', 'image/gif', 'image/bmp'
    ])
    
    # Check if file has content_type attribute (from InMemoryUploadedFile)
    if hasattr(value, 'content_type'):
        if value.content_type not in valid_mime_types:
            raise ValidationError(
                f'Invalid file type. Allowed: {", ".join(valid_mime_types)}'
            )
    
    return value
