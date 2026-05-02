from django.core.management.base import BaseCommand
from django.utils import timezone
from equipment.models import Equipment
from notifications.models import Notification
from accounts.models import User

class Command(BaseCommand):
    help = 'Checks for equipment with warranties expiring soon and creates notifications'

    def handle(self, *args, **options):
        today = timezone.now().date()
        expiring_soon_threshold = today + timezone.timedelta(days=30)
        
        # Find equipment with warranty expiring in the next 30 days
        expiring_equipment = Equipment.objects.filter(
            warranty_expiry__gte=today,
            warranty_expiry__lte=expiring_soon_threshold
        ).select_related('brand')
        
        it_admins = User.objects.filter(role='IT_ADMIN')
        
        count = 0
        for eq in expiring_equipment:
            message = f"Warranty for {eq.brand.name} {eq.model_number} ({eq.tracking_id}) expires on {eq.warranty_expiry}."
            
            for admin in it_admins:
                Notification.objects.get_or_create(
                    recipient=admin,
                    title="Warranty Expiry Alert",
                    message=message,
                    notification_type='SYSTEM',
                    related_id=str(eq.id)
                )
            count += 1
            
        self.stdout.write(self.style.SUCCESS(f'Processed {count} expiring warranties'))
