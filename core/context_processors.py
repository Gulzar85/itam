# context_processors.py
from .models import BusinessInfo
from notifications.models import Notification


def business_context(request):
    business = BusinessInfo.objects.filter(is_active=True).first()

    unread_notifications_count = 0
    if request.user.is_authenticated:
        unread_notifications_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()

    return {
        'business_info': business,
        'unread_count': unread_notifications_count,
    }


def page_context(request):
    url_name = request.resolver_match.url_name if request.resolver_match else 'dashboard'

    page_titles = {
        'dashboard': {'title': 'Dashboard', 'subtitle': 'Overview & Recent Activity'},
        'create': {'title': 'New Request', 'subtitle': 'Submit IT Equipment Request'},
        'index': {'title': 'Dashboard', 'subtitle': 'Overview & Recent Activity'},
        'equipment:equipment_list': {'title': 'Equipment', 'subtitle': 'Manage IT Assets'},
        'equipment:equipment_detail': {'title': 'Equipment Details', 'subtitle': 'View Asset Information'},
        'equipment:equipment_create': {'title': 'Add Equipment', 'subtitle': 'Register New Asset'},
        'equipment:equipment_update': {'title': 'Edit Equipment', 'subtitle': 'Update Asset Details'},
        'equipment:vendor_list': {'title': 'Vendors', 'subtitle': 'Manage Suppliers & Services'},
        'equipment:vendor_detail': {'title': 'Vendor Details', 'subtitle': 'View Vendor Info'},
        'equipment:vendor_create': {'title': 'Add Vendor', 'subtitle': 'Register New Vendor'},
        'equipment:vendor_update': {'title': 'Edit Vendor', 'subtitle': 'Update Vendor'},
        'equipment:brand_list': {'title': 'Brands', 'subtitle': 'Manage Equipment Brands'},
        'equipment:brand_detail': {'title': 'Brand Details', 'subtitle': 'View Brand Info'},
        'equipment:brand_create': {'title': 'Add Brand', 'subtitle': 'Register New Brand'},
        'equipment:brand_update': {'title': 'Edit Brand', 'subtitle': 'Update Brand'},
        'equipment:category_list': {'title': 'Categories', 'subtitle': 'Manage Equipment Categories'},
        'equipment:category_detail': {'title': 'Category Details', 'subtitle': 'View Category Info'},
        'equipment:category_create': {'title': 'Add Category', 'subtitle': 'Register New Category'},
        'equipment:category_update': {'title': 'Edit Category', 'subtitle': 'Update Category'},
        'requests:manager_approvals': {'title': 'Approvals', 'subtitle': 'Pending Requests'},
        'requests:detail': {'title': 'Request Details', 'subtitle': 'View Request Information'},
        'requests:create': {'title': 'New Request', 'subtitle': 'Submit IT Equipment Request'},
        'requests:equipment_assign': {'title': 'Assign Equipment', 'subtitle': 'Asset Assignment'},
        'requests:assign_new': {'title': 'Assign Equipment', 'subtitle': 'Asset Assignment'},
        'requests:manager_approvals': {'title': 'Approvals', 'subtitle': 'Pending Requests'},
        'requests:detail': {'title': 'Request Details', 'subtitle': 'View Request Information'},
        'requests:create': {'title': 'New Request', 'subtitle': 'Submit IT Equipment Request'},
        'requests:equipment_assign': {'title': 'Assign Equipment', 'subtitle': 'Asset Assignment'},
        'requests:assign_new': {'title': 'Assign Equipment', 'subtitle': 'Asset Assignment'},
        'notifications:list': {'title': 'Notifications', 'subtitle': 'Your Alerts & Updates'},
        'notifications:detail': {'title': 'Notification Details', 'subtitle': 'View Notification'},
        'core:business_info': {'title': 'Business Info', 'subtitle': 'Company Settings'},
        'core:business_info_update': {'title': 'Edit Business Info', 'subtitle': 'Update Settings'},
        'core:social_media_list': {'title': 'Social Media', 'subtitle': 'Manage Social Links'},
        'core:social_media_create': {'title': 'Add Social Link', 'subtitle': 'New Social Link'},
        'core:social_media_update': {'title': 'Edit Social Link', 'subtitle': 'Update Social Link'},
        'equipment:dashboard_report': {'title': 'Analytics Report', 'subtitle': 'Charts & Visual Insights'},
        'equipment:comprehensive_report': {'title': 'Comprehensive Report', 'subtitle': 'Detailed Equipment Data'},
        'equipment:maintenance_report': {'title': 'Maintenance History', 'subtitle': 'Repair Records'},
        'equipment:request_summary_report': {'title': 'Request Summary', 'subtitle': 'All IT Requests'},
        'equipment:turnaround_report': {'title': 'Turnaround Report', 'subtitle': 'Processing Time Analysis'},
        'equipment:vendor_performance_report': {'title': 'Vendor Performance', 'subtitle': 'Vendor Metrics'},
        'equipment:department_report': {'title': 'Department Distribution', 'subtitle': 'Equipment Allocation'},
        'equipment:inventory_list': {'title': 'Inventory', 'subtitle': 'Manage IT Assets'},
        'accounts:profile': {'title': 'Profile', 'subtitle': 'Your Account Settings'},
        'accounts:profile_edit': {'title': 'Edit Profile', 'subtitle': 'Update Account'},
        'accounts:change_password': {'title': 'Change Password', 'subtitle': 'Update Password'},
        'accounts:login': {'title': 'Login', 'subtitle': 'Sign In'},
        'accounts:register': {'title': 'Register', 'subtitle': 'Create Account'},
    }

    app_name = request.resolver_match.app_name if request.resolver_match else ''
    url_name = request.resolver_match.url_name if request.resolver_match else 'dashboard'

    if app_name and url_name:
        full_url_name = f"{app_name}:{url_name}"
    else:
        full_url_name = url_name

    page_data = page_titles.get(full_url_name) or page_titles.get(url_name) or {}

    if not page_data and 'list' in url_name:
        url_list = url_name.replace('list', '')
        page_data = page_titles.get(f"{app_name}:{url_list}") or {}

    page_title = page_data.get('title', 'Dashboard')
    page_subtitle = page_data.get('subtitle', 'Welcome back')

    return {
        'page_title': page_title,
        'page_subtitle': page_subtitle,
    }
