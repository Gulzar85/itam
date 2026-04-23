from django.contrib import admin
from .models import Request, RequestLog, Assignment


class RequestLogInline(admin.TabularInline):
    model = RequestLog
    extra = 0
    readonly_fields = ('action_by', 'old_status',
                       'new_status', 'remarks', 'timestamp')
    can_delete = False


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'request_type',
                    'priority', 'status', 'created_at')
    search_fields = ('user__username', 'reason')
    inlines = [RequestLogInline]

    # Admin se status change karte waqt logic control
    def save_model(self, request, obj, form, change):
        if change:
            # Yahan hum logging logic daal sakte hain (T5 mein detail se karenge)
            pass
        super().save_model(request, obj, form, change)


@admin.register(RequestLog)
class RequestLogAdmin(admin.ModelAdmin):
    list_display = ('request', 'action_by', 'old_status',
                    'new_status', 'timestamp')
    search_fields = ('request__id', 'action_by__username')
    readonly_fields = ('request', 'action_by', 'old_status',
                       'new_status', 'remarks', 'timestamp')

    def has_add_permission(self, request):
        return False  # Admin se direct log add nahi kar sakte


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'user', 'assigned_date', 'returned_date')
    search_fields = ('equipment__model_number', 'user__username')
    readonly_fields = ('equipment', 'user', 'assigned_date',
                       'returned_date', 'notes')
