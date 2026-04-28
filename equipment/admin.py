from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.translation import gettext_lazy as _
from .models import Equipment, Vendor, Brand, Category, EquipmentLog, MaintenanceRecord


class StatusFilter(SimpleListFilter):
    title = _('Equipment Status')
    parameter_name = 'status_filter'

    def lookups(self, request, model_admin):
        return Equipment.STATUS_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


class EquipmentAgeFilter(SimpleListFilter):
    title = _('Equipment Age')
    parameter_name = 'age'

    def lookups(self, request, model_admin):
        return (
            ('0-1', 'Under 1 year'),
            ('1-3', '1-3 years'),
            ('3-5', '3-5 years'),
            ('5+', 'Over 5 years'),
        )

    def queryset(self, request, queryset):
        from django.utils import timezone
        today = timezone.now().date()
        if self.value() == '0-1':
            return queryset.filter(purchase_date__gte=today.replace(year=today.year-1))
        if self.value() == '1-3':
            return queryset.filter(
                purchase_date__lt=today.replace(year=today.year-1),
                purchase_date__gte=today.replace(year=today.year-3)
            )
        if self.value() == '3-5':
            return queryset.filter(
                purchase_date__lt=today.replace(year=today.year-3),
                purchase_date__gte=today.replace(year=today.year-5)
            )
        if self.value() == '5+':
            return queryset.filter(purchase_date__lt=today.replace(year=today.year-5))
        return queryset


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('tracking_id', 'brand', 'model_number', 'serial_number', 'status', 'assigned_to', 'purchase_date')
    list_filter = (StatusFilter, 'category', 'brand', EquipmentAgeFilter, 'purchase_date')
    search_fields = ('tracking_id', 'serial_number', 'model_number', 'brand__name')
    readonly_fields = ('tracking_id', 'created_at', 'updated_at', 'qr_code_preview')
    list_per_page = 25

    def qr_code_preview(self, obj):
        if obj.qr_code:
            from django.utils.html import format_html
            return format_html('<img src="{}" width="150" />', obj.qr_code.url)
        return "(No QR code)"
    qr_code_preview.short_description = "QR Code Preview"

    actions = ['mark_as_damaged', 'mark_as_available']

    def mark_as_damaged(self, request, queryset):
        updated = queryset.update(status='DAMAGED')
        self.message_user(request, f'{updated} items marked as damaged.')
    mark_as_damaged.short_description = "Mark selected as Damaged"

    def mark_as_available(self, request, queryset):
        updated = queryset.filter(status='REPAIRING').update(status='AVAILABLE')
        self.message_user(request, f'{updated} items marked as available.')
    mark_as_available.short_description = "Mark repaired items as Available"


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'vendor_type', 'contact_person', 'phone', 'email', 'rating')
    list_filter = ('vendor_type',)
    search_fields = ('name', 'contact_person', 'email')


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'website', 'support_contact')
    search_fields = ('name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'description')
    search_fields = ('name',)


@admin.register(EquipmentLog)
class EquipmentLogAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'action_by', 'old_status', 'new_status', 'timestamp')
    list_filter = ('old_status', 'new_status', 'timestamp')
    search_fields = ('equipment__tracking_id', 'equipment__serial_number')
    date_hierarchy = 'timestamp'


@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'vendor', 'status', 'sent_date', 'expected_return_date', 'actual_return_date')
    list_filter = ('status', 'vendor', 'sent_date')
    search_fields = ('equipment__tracking_id', 'equipment__serial_number', 'issue_description')
    date_hierarchy = 'sent_date'
