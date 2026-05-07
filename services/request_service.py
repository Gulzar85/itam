from django.db import transaction
from django.utils import timezone
from requests.models import Request, RequestLog
from equipment.models import Equipment, EquipmentLog
from services.request_workflow import can_actor_transition, get_valid_statuses


class RequestService:
    @staticmethod
    @transaction.atomic
    def update_request_status(request_obj, new_status, action_by, remarks="", equipment_obj=None):
        """
    Universal handler for IT Asset Workflow.
    Status transitions follow the defined workflow sequence.
    """
        old_status = request_obj.status
        valid_statuses = get_valid_statuses()
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}")
        if old_status == new_status:
            raise ValueError("Request is already in the specified status")
        if not can_actor_transition(action_by, request_obj, new_status):
            raise PermissionError("Actor is not allowed to apply this transition")

        # 1. NEW ASSIGNMENT LOGIC (For New/Replacement Requests)
        if equipment_obj and new_status == 'COMPLETED':
            request_obj.equipment = equipment_obj
            equipment_obj.status = 'ASSIGNED'
            equipment_obj.assigned_to = request_obj.user
            equipment_obj.assigned_date = timezone.now().date()
            equipment_obj.save()

            EquipmentLog.objects.create(
                equipment=equipment_obj,
                action_by=action_by,
                old_status='AVAILABLE',
                new_status='ASSIGNED',
                remarks=f"Asset assigned to user via Request #{request_obj.id}"
            )

        # 2. REPAIR/MAINTENANCE LOGIC (Asset remains with the user)
        elif request_obj.equipment and request_obj.request_type == 'REPAIR':
            eq = request_obj.equipment
            old_eq_status = eq.status

            # Step: Admin selects vendor (Status becomes IN_PROGRESS)
            if new_status == 'IN_PROGRESS':
                eq.status = 'REPAIRING'
                eq.save()

                EquipmentLog.objects.create(
                    equipment=eq,
                    action_by=action_by,
                    old_status=old_eq_status,
                    new_status='REPAIRING',
                    remarks=f"Sent to vendor for maintenance. Still tagged to {request_obj.user.get_full_name()}."
                )

            # Step: Admin completes repair (Status becomes COMPLETED)
            elif new_status == 'COMPLETED':
                eq.status = 'ASSIGNED'
                eq.save()

                EquipmentLog.objects.create(
                    equipment=eq,
                    action_by=action_by,
                    old_status=old_eq_status,
                    new_status='ASSIGNED',
                    remarks=f"Maintenance completed. Asset verified and kept with {request_obj.user.get_full_name()}."
                )

        # 3. UNIVERSAL STATUS UPDATE
        # Manager jab approve karega to new_status 'MANAGER_APPROVED' aayega
        # IT Admin jab vendor set karega to new_status 'IN_PROGRESS' aayega
        request_obj.status = new_status
        request_obj.save()

        # 4. CREATE AUDIT LOG
        RequestLog.objects.create(
            request=request_obj,
            action_by=action_by,
            old_status=old_status,
            new_status=new_status,
            remarks=remarks or f"Request status updated to {new_status.replace('_', ' ').title()}"
        )

        return request_obj

    @staticmethod
    def create_new_request(user, request_type, category, brand=None, equipment=None, reason=""):
        """Initial request creation with standard English logs."""
        request_obj = Request.objects.create(
            user=user,
            request_type=request_type,
            category_needed=category,
            brand_preference=brand,
            equipment=equipment,
            reason=reason,
            status='PENDING'
        )
        RequestLog.objects.create(
            request=request_obj,
            action_by=user,
            old_status='NONE',
            new_status='PENDING',
            remarks="Request submitted and awaiting manager approval."
        )
        return request_obj
