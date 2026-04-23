from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import date
from .models import Assignment, Request, RequestLog
from notifications.models import Notification
from equipment.models import EquipmentLog


@receiver(post_save, sender=Assignment)
def handle_full_assignment_workflow(sender, instance, created, **kwargs):
    if created:
        equipment = instance.equipment
        user = instance.user  # Recipient
        admin = instance.assigned_by

        old_eq_status = equipment.status

        # 1. Update Equipment Table
        equipment.status = 'ASSIGNED'
        equipment.assigned_to = user
        equipment.assigned_date = date.today()
        equipment.save()

        # 2. Create Equipment Log (With proper Admin and Old Status)
        EquipmentLog.objects.create(
            equipment=equipment,
            action_by=admin,
            old_status=old_eq_status,
            new_status='ASSIGNED',
            remarks=f"Asset assigned to {user.get_full_name()} (Assignment ID: {instance.id})"
        )

        # 3. Close Related Request & Create Request Log
        related_request = Request.objects.filter(
            user=user,
            equipment=equipment,
            status__in=['PENDING', 'MANAGER_APPROVED',
                        'IT_RECEIVED', 'IN_PROGRESS']
        ).first()

        if related_request:
            old_req_status = related_request.status
            related_request.status = 'COMPLETED'
            related_request.save()

            # Create Request Log
            RequestLog.objects.create(
                request=related_request,
                action_by=admin,
                old_status=old_req_status,
                new_status='COMPLETED',
                remarks=f"Request automatically completed via Assignment {instance.id}"
            )

        # 4. Trigger Notification
        Notification.objects.create(
            recipient=user,
            notification_type='EQUIPMENT_ASSIGNED',
            title="Equipment Assigned to You",
            message=f"The {equipment.category.name} ({equipment.brand.name} {equipment.model_number}) has been assigned to you. Serial: {equipment.serial_number}",
            priority='HIGH',
            related_request=related_request,
            related_equipment=equipment
        )
