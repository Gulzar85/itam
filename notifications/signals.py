from django.db.models.signals import post_save
from django.dispatch import receiver
from requests.models import Request, RequestLog
from notifications.models import Notification
from django.core.mail import send_mail
from django.conf import settings


@receiver(post_save, sender=Request)
def notify_request_status_change(sender, instance, created, **kwargs):
    """
    Jab request ka status update ho, to user ko notification aur email bhejein.
    """
    if not created:  # Sirf update hone per notify kare
        # Create notification for the request owner
        Notification.objects.create(
            recipient=instance.user,
            notification_type='REQUEST_APPROVED',  # Use valid notification type
            title=f"Request #{instance.request_id} Status Updated",
            message=f"Your {instance.request_type.lower()} request status has been updated to: {instance.get_status_display()}",
            priority='MEDIUM',
            related_request=instance
        )

        # Notify manager if status changed to PENDING (new request)
        if instance.status == 'PENDING':
            if hasattr(instance.user, 'manager') and instance.user.manager:
                Notification.objects.create(
                    recipient=instance.user.manager,
                    notification_type='REQUEST_CREATED',
                    title=f"New Request from {instance.user.get_full_name() or instance.user.username}",
                    message=f"{instance.user.get_full_name() or instance.user.username} has submitted a new {instance.request_type.lower()} request requiring your approval.",
                    priority='HIGH',
                    related_request=instance
                )

        # Notify IT admin when request is approved by manager
        elif instance.status == 'MANAGER_APPROVED':
            from accounts.models import User
            it_admins = User.objects.filter(role='IT_ADMIN')
            for admin in it_admins:
                Notification.objects.create(
                    recipient=admin,
                    notification_type='REQUEST_APPROVED',
                    title=f"Request #{instance.request_id} Approved",
                    message=f"{instance.user.get_full_name() or instance.user.username}'s request has been approved by manager and is ready for IT processing.",
                    priority='HIGH',
                    related_request=instance
                )

        # Notify user when request is completed
        elif instance.status == 'COMPLETED':
            Notification.objects.create(
                recipient=instance.user,
                notification_type='REQUEST_COMPLETED',
                title=f"Request #{instance.request_id} Completed",
                message=f"Your {instance.request_type.lower()} request has been completed successfully.",
                priority='MEDIUM',
                related_request=instance
            )

        # Notify user when request is rejected
        elif instance.status == 'REJECTED':
            Notification.objects.create(
                recipient=instance.user,
                notification_type='REQUEST_REJECTED',
                title=f"Request #{instance.request_id} Rejected",
                message=f"Your {instance.request_type.lower()} request has been rejected. Please check the details for more information.",
                priority='HIGH',
                related_request=instance
            )


@receiver(post_save, sender=RequestLog)
def notify_request_action(sender, instance, created, **kwargs):
    """
    Jab koi action log create ho, to relevant parties ko notify karein.
    """
    if created:
        # Notify the action performer about successful action
        if instance.action_by != instance.request.user:
            Notification.objects.create(
                recipient=instance.action_by,
                notification_type='ACTION_PERFORMED',
                title=f"Action completed on Request #{instance.request.request_id}",
                message=f"You have successfully updated the request status from {instance.old_status.title()} to {instance.new_status.title()}.",
                priority='LOW',
                related_request=instance.request
            )
