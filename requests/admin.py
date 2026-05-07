from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Request, RequestLog, Assignment


class StatusFilter(admin.SimpleListFilter):
    title = _('Request Status')
    parameter_name = 'status_filter'

    def lookups(self, request, model_admin):
        return Request.STATUS_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


class PriorityFilter(admin.SimpleListFilter):
    title = _('Priority')
    parameter_name = 'priority_filter'

    def lookups(self, request, model_admin):
        return Request.PRIORITY_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(priority=self.value())
        return queryset


class RequestTypeFilter(admin.SimpleListFilter):
    title = _('Request Type')
    parameter_name = 'type_filter'

    def lookups(self, request, model_admin):
        return Request.REQUEST_TYPE_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(request_type=self.value())
        return queryset


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('request_id', 'user', 'request_type', 'priority', 'status', 'equipment', 'created_at')
    list_filter = (StatusFilter, PriorityFilter, RequestTypeFilter, 'created_at')
    search_fields = ('request_id', 'user__username', 'reason', 'equipment__tracking_id')
    readonly_fields = ('request_id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    list_per_page = 25

    actions = ['mark_as_completed', 'mark_as_rejected']

    def mark_as_completed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status__in=['IN_PROGRESS', 'READY']).update(
            status='COMPLETED',
            updated_at=timezone.now()
        )
        self.message_user(request, f'{updated} requests marked as completed.')
    mark_as_completed.short_description = "Mark as Completed"

    def mark_as_rejected(self, request, queryset):
        updated = queryset.filter(status='PENDING').update(status='REJECTED')
        self.message_user(request, f'{updated} requests rejected.')
    mark_as_rejected.short_description = "Reject Pending Requests"


@admin.register(RequestLog)
class RequestLogAdmin(admin.ModelAdmin):
    list_display = ('request', 'action_by', 'old_status', 'new_status', 'timestamp')
    list_filter = ('old_status', 'new_status', 'timestamp')
    search_fields = ('request__request_id', 'remarks')
    date_hierarchy = 'timestamp'


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'user', 'assigned_date', 'assigned_by')
    list_filter = ('assigned_date',)
    search_fields = ('equipment__tracking_id', 'user__username')
    date_hierarchy = 'assigned_date'
