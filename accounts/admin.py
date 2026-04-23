from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Department


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Admin list mein ye columns dikhayen gay
    list_display = ('username', 'email', 'role', 'manager', 'is_staff')
    list_filter = ('role', 'department')

    # User edit screen mein fields ka izafa
    fieldsets = (
        *UserAdmin.fieldsets,
        ('Professional Info', {
            'fields': ('role', 'manager', 'department', 'phone_number')
        }),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
