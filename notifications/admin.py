from django.contrib import admin
from .models import Notification, NotificationTemplate


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'title',
                    'priority', 'is_read', 'created_at')
    list_filter = ('notification_type', 'priority',
                   'is_read', 'is_archived', 'created_at')
    search_fields = ('recipient__username', 'title', 'message')
    readonly_fields = ('id', 'created_at', 'read_at')

    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'recipient', 'notification_type', 'title', 'message', 'priority')
        }),
        ('Related Objects', {
            'fields': ('related_request', 'related_equipment')
        }),
        ('Status', {
            'fields': ('is_read', 'is_archived', 'read_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('notification_type', 'subject_template', 'is_active')
    list_filter = ('notification_type', 'is_active')
    search_fields = ('notification_type',
                     'subject_template', 'message_template')

    fieldsets = (
        ('Template Info', {
            'fields': ('notification_type', 'subject_template', 'message_template', 'is_active')
        }),
    )
