from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
from .models import Request
from equipment.models import Equipment, Category, MaintenanceRecord


def get_advanced_dashboard_stats():
    # 1. Trend Data (Last 6 Months)
    six_months_ago = timezone.now() - timedelta(days=180)
    trends = (
        Request.objects.filter(created_at__gte=six_months_ago)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    # 2. Asset Distribution (By Category)
    category_dist = (
        Category.objects.annotate(asset_count=Count('equipments'))
        .filter(asset_count__gt=0)
        .values('name', 'asset_count')
    )

    # 3. Maintenance Spend by Category (Real Cost Data)
    cost_dist = (
        MaintenanceRecord.objects.values('equipment__category__name')
        .annotate(total_cost=Sum('actual_cost'))
        .filter(total_cost__gt=0)
    )

    # 4. Asset Health (Status Distribution)
    health_dist = (
        Equipment.objects.values('status')
        .annotate(total=Count('id'))
    )

    return {
        'trends': {
            'months': [t['month'].strftime('%b %Y') for t in trends],
            'counts': [t['count'] for t in trends]
        },
        'categories': {
            'labels': [c['name'] for c in category_dist],
            'series': [c['asset_count'] for c in category_dist]
        },
        'costs': {
            'labels': [cost['equipment__category__name'] for cost in cost_dist],
            'series': [float(cost['total_cost'] or 0) for cost in cost_dist]
        },
        'health': {
            'labels': [h['status'].replace('_', ' ').title() for h in health_dist],
            'series': [h['total'] for h in health_dist]
        }
    }
