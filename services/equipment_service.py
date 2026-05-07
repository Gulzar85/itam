from django.db import transaction
from django.utils import timezone
from django.core.files import File
from io import BytesIO
import qrcode
from equipment.models import Equipment, EquipmentLog
from core.models import SequenceCounter

class EquipmentService:
    @staticmethod
    def generate_tracking_id():
        """Generates a custom ID like EQ-2026-0001 using atomic counter"""
        year = timezone.now().year
        prefix = 'EQ'
        next_value = SequenceCounter.get_next_value(prefix, year)
        return f"{prefix}-{year}-{str(next_value).zfill(4)}"

    @staticmethod
    def generate_qr_code(equipment):
        """Generates QR code image for equipment"""
        qr_content = f"EQ:{equipment.tracking_id}\nSN:{equipment.serial_number}\nModel:{equipment.model_number}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_content)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        filename = f'qr-{equipment.tracking_id}.png'
        equipment.qr_code.save(filename, File(buffer), save=False)

    @staticmethod
    @transaction.atomic
    def update_equipment_status(equipment, new_status, action_by, remarks="Status updated"):
        """Updates equipment status with audit logging and business rules"""
        old_status = equipment.status
        
        # Apply business rules for status transitions
        if new_status == 'AVAILABLE':
            equipment.assigned_to = None
            equipment.assigned_date = None
            equipment.current_repair_vendor = None
        elif new_status == 'ASSIGNED' and not equipment.assigned_to:
            # Prevent moving to ASSIGNED without an owner
            new_status = 'AVAILABLE'
            
        equipment.status = new_status
        equipment.save()
        
        # Create audit log
        EquipmentLog.objects.create(
            equipment=equipment,
            action_by=action_by,
            old_status=old_status,
            new_status=new_status,
            remarks=remarks
        )
        
        return equipment
