from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
import uuid

phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
)


class Department(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    # Role Constants
    IS_EMPLOYEE = 'EMPLOYEE'
    IS_MANAGER = 'MANAGER'
    IS_IT_ADMIN = 'IT_ADMIN'

    ROLE_CHOICES = [
        (IS_EMPLOYEE, 'Employee'),
        (IS_MANAGER, 'Manager'),
        (IS_IT_ADMIN, 'IT Admin'),
    ]

    # Role identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default=IS_EMPLOYEE)
    # 'self' means a user points to another user as their manager.
    manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='team_members'
    )
    email = models.EmailField(unique=True)
    phone_number = models.CharField(
        max_length=15, blank=True, null=True, validators=[phone_regex], help_text="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def is_line_manager(self):
        """Check if this user manages anyone"""
        return getattr(self, 'team_members').exists()
