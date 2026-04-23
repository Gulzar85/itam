from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Category, Brand, Vendor, Equipment, EquipmentLog, MaintenanceRecord


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    # Added tracking_id and QR preview to the list
    list_display = ('tracking_id', 'serial_number', 'brand', 'model_number',
                    'category', 'status', 'display_qr_tiny')

    # Enable search for tracking_id and serial number
    search_fields = ('tracking_id', 'serial_number', 'model_number')

    # Filter by status and category for easier management
    list_filter = ('status', 'category', 'brand')

    # Important: tracking_id and qr_code must be readonly because they are auto-generated
    readonly_fields = ('tracking_id', 'display_qr_large')

    fieldsets = (
        ('Identification', {
            'fields': ('tracking_id', 'display_qr_large')
        }),
        ('Technical Specs', {
            'fields': ('category', 'brand', 'model_number', 'serial_number')
        }),
        ('Vendor & Warranty', {
            'fields': ('original_vendor', 'purchase_date', 'warranty_expiry')
        }),
        ('Status & Support', {
            'fields': ('status', 'current_repair_vendor', 'image', 'assigned_to')
        }),
    )

    # Helper function to show a small QR code in the list view
    def display_qr_tiny(self, obj):
        if obj.qr_code:
            return mark_safe(f'<img src="{obj.qr_code.url}" width="35" height="35" />')
        return "-"
    display_qr_tiny.short_description = 'QR'

    # Helper function to show a large QR code in the detail view
    def display_qr_large(self, obj):
        if obj.qr_code:
            return mark_safe(f'<img src="{obj.qr_code.url}" width="150" height="150" />')
        return "Will be generated after saving."
    display_qr_large.short_description = 'QR Code Preview'


admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(Vendor)
admin.site.register(EquipmentLog)
admin.site.register(MaintenanceRecord)
