# admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import BusinessInfo, SocialMediaLink


@admin.register(BusinessInfo)
class BusinessInfoAdmin(admin.ModelAdmin):
    list_display = ['logo_preview', 'name',
                    'contact_email', 'contact_phone', 'is_active']
    search_fields = ['name', 'contact_email', 'contact_phone']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at', 'logo_preview']

    class Media:
        css = {
            'all': ('admin/css/admin-custom.css',)
        }

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 8px;" />', obj.logo.url)
        return "No logo"
    logo_preview.short_description = 'Logo'


@admin.register(SocialMediaLink)
class SocialMediaLinkAdmin(admin.ModelAdmin):
    list_display = ['icon_preview', 'get_platform_display', 'business', 'url']
    search_fields = ['business__name', 'url']

    class Media:
        css = {
            'all': ('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',)
        }

    def icon_preview(self, obj):
        return format_html(
            '<i class="{}" style="font-size: 20px; width: 30px;"></i>',
            obj.icon_class
        )
    icon_preview.short_description = 'Icon'

    def get_platform_display(self, obj):
        return obj.get_platform_display()
    get_platform_display.short_description = 'Platform'
