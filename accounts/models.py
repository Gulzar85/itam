import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils.functional import cached_property

phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
)


class Department(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, db_index=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    # Role Constants - Only EMPLOYEE or IT_ADMIN
    IS_EMPLOYEE = 'EMPLOYEE'
    IS_IT_ADMIN = 'IT_ADMIN'

    ROLE_CHOICES = [
        (IS_EMPLOYEE, 'Employee'),
        (IS_IT_ADMIN, 'IT Admin'),
    ]

    # Role identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, db_default=IS_EMPLOYEE, db_index=True)
    
    # employee -> manager relationship
    # manager can approve their direct reports' requests
    manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='team_members',
        help_text="Select the manager this employee reports to. Managers can approve requests from their direct reports.",
        db_index=True
    )
    email = models.EmailField(unique=True, db_index=True)
    phone_number = models.CharField(
        max_length=15, blank=True, null=True, validators=[phone_regex], help_text="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def is_manager(self):
        """Check if this user is a manager (has team members reporting to them)"""
        return self.team_members.exists()

    @property
    def can_approve(self):
        """Check if this user can approve requests - true if they are a manager with team members"""
        return self.is_manager or self.role == self.IS_IT_ADMIN
