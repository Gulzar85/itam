from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils import timezone
from .models import Notification


class NotificationListView(LoginRequiredMixin, ListView):
    """Display user's notifications"""
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user,
            is_archived=False
        ).order_by('-created_at')


class NotificationDetailView(LoginRequiredMixin, DetailView):
    """Display notification details"""
    model = Notification
    template_name = 'notifications/notification_detail.html'
    context_object_name = 'notification'

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # Mark as read when viewed
        if not self.object.is_read:
            self.object.mark_as_read()
        return response


class MarkAsReadView(LoginRequiredMixin, View):
    """AJAX view to mark notification as read"""

    def post(self, request, pk):
        notification = get_object_or_404(
            Notification,
            pk=pk,
            recipient=request.user
        )
        notification.mark_as_read()
        return JsonResponse({'status': 'success'})


class MarkAllAsReadView(LoginRequiredMixin, View):
    """Mark all user's notifications as read"""

    def post(self, request):
        Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        return JsonResponse({'status': 'success'})


class ArchiveNotificationView(LoginRequiredMixin, View):
    """Archive a notification"""

    def post(self, request, pk):
        notification = get_object_or_404(
            Notification,
            pk=pk,
            recipient=request.user
        )
        notification.is_archived = True
        notification.save()
        return JsonResponse({'status': 'success'})


class NotificationCountView(LoginRequiredMixin, View):
    """Get unread notification count for AJAX updates"""

    def get(self, request):
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
            is_archived=False
        ).count()
        return JsonResponse({'count': count})
