from .models import Brand, Category, Equipment, MaintenanceRecord, Vendor
from requests.models import Request, Assignment
from django.utils.timezone import now as utc_now, make_aware
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.db.models.functions import Coalesce, TruncMonth, Cast
from django.db.models import Count, Q, Sum, F, ExpressionWrapper, IntegerField, DecimalField
from decimal import Decimal
from django.utils.timezone import now as utc_now
from accounts.models import Department
from .models import Equipment, Brand, Category, MaintenanceRecord
from django.views.generic import TemplateView
from django.utils.timezone import make_aware
from django.db.models.functions import TruncMonth, Coalesce
from datetime import datetime
import csv
import json
from datetime import datetime, timedelta
from typing import Any

from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.timezone import make_aware, now
from django.views import View
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView
)

from services.permissions import ITAdminRequiredMixin

from requests.models import Request
from requests.utils import get_advanced_dashboard_stats

from .forms import BrandForm, CategoryForm, EquipmentForm, VendorForm
from .models import Brand, Category, Equipment, EquipmentLog, MaintenanceRecord, Vendor
from equipment.models import Category  # noqa: F401


class EquipmentListView(LoginRequiredMixin, ListView):
    """List all equipment with dynamic stats, filtering and search"""
    model = Equipment
    template_name = 'equipment/equipment_list.html'
    context_object_name = 'equipment_list'
    paginate_by = 9

    def get_queryset(self):
        queryset = Equipment.objects.select_related(
            'brand', 'category', 'original_vendor', 'current_repair_vendor'
        )

        search = self.request.GET.get('search')
        if search:
            # Clean QR code format (e.g., "EQ:EQ-2026-0001" or "SN:DELL-001")
            search = search.replace('EQ:', '').replace('SN:', '').strip()

            queryset = queryset.filter(
                Q(serial_number__icontains=search) |
                Q(tracking_id__icontains=search) |
                Q(model_number__icontains=search) |
                Q(brand__name__icontains=search) |
                Q(category__name__icontains=search)
            )

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)

        return queryset.order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base_qs = Equipment.objects.all()

        context['total_count'] = base_qs.count()
        context['available_count'] = base_qs.filter(status='AVAILABLE').count()
        context['repairing_count'] = base_qs.filter(status='REPAIRING').count()
        context['assigned_count'] = base_qs.filter(status='ASSIGNED').count()

        context['categories'] = Category.objects.all()
        context['status_choices'] = Equipment.STATUS_CHOICES
        context['today'] = now().date()

        return context


class EquipmentDetailView(LoginRequiredMixin, DetailView):
    model = Equipment
    template_name = 'equipment/equipment_detail.html'
    context_object_name = 'equipment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = now().date()

        # Get equipment logs chronologically
        logs = list(self.object.logs.all().order_by('timestamp'))

        # Add virtual "registered" log at the beginning if not exists
        if logs and logs[0].old_status != 'NEW':
            registered_log = type('obj', (object,), {
                'timestamp': self.object.purchase_date or self.object.created_at,
                'action_by': None,
                'status': 'NEW',
                'new_status': 'AVAILABLE',
                'remarks': f'Equipment registered in system'
            })()
            logs.insert(0, registered_log)

        context['logs'] = logs

        from requests.models import Assignment
        context['current_assignment'] = Assignment.objects.filter(
            equipment=self.object
        ).order_by('-assigned_date').first()

        # Get maintenance history for this equipment
        from equipment.models import MaintenanceRecord
        context['maintenance_records'] = MaintenanceRecord.objects.filter(
            equipment=self.object
        ).select_related('vendor', 'request', 'request__user').order_by('-sent_date')

        # Get past assignments
        context['past_assignments'] = Assignment.objects.filter(
            equipment=self.object
        ).select_related('user', 'user__department').order_by('-assigned_date')

        return context


class EquipmentCreateView(LoginRequiredMixin, ITAdminRequiredMixin, SuccessMessageMixin, CreateView):
    """Create new equipment"""
    model = Equipment
    form_class = EquipmentForm
    template_name = 'equipment/equipment_form.html'
    success_url = reverse_lazy('equipment:equipment_list')
    success_message = "Equipment has been created successfully!"

    def form_valid(self, form):
        if not form.cleaned_data.get('status'):
            form.instance.status = 'AVAILABLE'
        return super().form_valid(form)


class EquipmentUpdateView(LoginRequiredMixin, ITAdminRequiredMixin, SuccessMessageMixin, UpdateView):
    """Update existing equipment"""
    model = Equipment
    form_class = EquipmentForm
    template_name = 'equipment/equipment_form.html'
    success_url = reverse_lazy('equipment:equipment_list')
    success_message = "Equipment has been updated successfully!"


class EquipmentDeleteView(LoginRequiredMixin, ITAdminRequiredMixin, SuccessMessageMixin, DeleteView):
    """Delete equipment"""
    model = Equipment
    template_name = 'equipment/equipment_confirm_delete.html'
    success_url = reverse_lazy('equipment:equipment_list')
    success_message = "Equipment has been deleted successfully!"


class EquipmentBulkActionView(LoginRequiredMixin, ITAdminRequiredMixin, View):
    """Handle bulk actions on equipment"""

    def post(self, request):
        action = request.POST.get('action')
        equipment_ids = request.POST.getlist('equipment_ids')

        if not action or not equipment_ids:
            return JsonResponse({'status': 'error', 'message': 'Missing action or equipment IDs'}, status=400)

        try:
            equipment_qs = Equipment.objects.filter(id__in=equipment_ids)

            if action == 'mark_damaged':
                count = equipment_qs.update(status='DAMAGED')
                return JsonResponse({'status': 'success', 'message': f'{count} items marked as damaged'})
            elif action == 'mark_available':
                count = equipment_qs.filter(
                    status='REPAIRING').update(status='AVAILABLE')
                return JsonResponse({'status': 'success', 'message': f'{count} items marked as available'})
            elif action == 'delete':
                count = equipment_qs.delete()[0]
                return JsonResponse({'status': 'success', 'message': f'{count} items deleted'})

            return JsonResponse({'status': 'error', 'message': 'Invalid action'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': 'Bulk action failed.'}, status=500)


class EquipmentExportView(LoginRequiredMixin, ITAdminRequiredMixin, View):
    """Export equipment list to CSV"""

    def get(self, request):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="equipment_export.csv"'

        writer = csv.writer(response)
        writer.writerow(['Tracking ID', 'Brand', 'Model', 'Serial Number',
                        'Category', 'Status', 'Assigned To', 'Purchase Date', 'Purchase Cost'])

        equipment = Equipment.objects.select_related(
            'brand', 'category', 'assigned_to').all()

        for eq in equipment:
            writer.writerow([
                eq.tracking_id,
                eq.brand.name if eq.brand else '',
                eq.model_number,
                eq.serial_number,
                eq.category.name if eq.category else '',
                eq.get_status_display(),
                eq.assigned_to.get_full_name() if eq.assigned_to else '',
                eq.purchase_date.strftime(
                    '%Y-%m-%d') if eq.purchase_date else '',
                float(eq.purchase_cost) if eq.purchase_cost else 0,
            ])

        return response


class EquipmentStatusUpdateView(LoginRequiredMixin, ITAdminRequiredMixin, View):
    """AJAX endpoint to update equipment status using EquipmentService"""

    def post(self, request, pk):
        from services.equipment_service import EquipmentService
        equipment = get_object_or_404(Equipment, pk=pk)
        new_status = request.POST.get('status')
        remarks = request.POST.get('remarks', 'Status updated via AJAX')

        if new_status in dict(Equipment.STATUS_CHOICES):
            EquipmentService.update_equipment_status(
                equipment=equipment,
                new_status=new_status,
                action_by=request.user,
                remarks=remarks
            )
            return JsonResponse({'status': 'success', 'message': f'Status updated to {new_status}'})

        return JsonResponse({'status': 'error', 'message': 'Invalid status'}, status=400)


# Vendor Views
class VendorListView(LoginRequiredMixin, ITAdminRequiredMixin, ListView):
    model = Vendor
    template_name = 'equipment/vendor_list.html'
    context_object_name = 'vendors'
    paginate_by = 10


class VendorDetailView(LoginRequiredMixin, ITAdminRequiredMixin, DetailView):
    model = Vendor
    template_name = 'equipment/vendor_detail.html'
    context_object_name = 'vendor'


class VendorCreateView(LoginRequiredMixin, ITAdminRequiredMixin, SuccessMessageMixin, CreateView):
    model = Vendor
    form_class = VendorForm
    template_name = 'equipment/vendor_form.html'
    success_url = reverse_lazy('equipment:vendor_list')
    success_message = "Vendor has been created successfully!"


class VendorUpdateView(LoginRequiredMixin, ITAdminRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Vendor
    form_class = VendorForm
    template_name = 'equipment/vendor_form.html'
    success_url = reverse_lazy('equipment:vendor_list')
    success_message = "Vendor has been updated successfully!"


class VendorDeleteView(LoginRequiredMixin, ITAdminRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Vendor
    template_name = 'equipment/vendor_confirm_delete.html'
    success_url = reverse_lazy('equipment:vendor_list')
    success_message = "Vendor has been deleted successfully!"


# Brand Views
class BrandListView(LoginRequiredMixin, ITAdminRequiredMixin, ListView):
    model = Brand
    template_name = 'equipment/brand_list.html'
    context_object_name = 'brands'
    paginate_by = 10


class BrandDetailView(LoginRequiredMixin, ITAdminRequiredMixin, DetailView):
    model = Brand
    template_name = 'equipment/brand_detail.html'
    context_object_name = 'brand'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        equipment_list = Equipment.objects.filter(brand=self.object)
        context['equipment_list'] = equipment_list
        context['available_count'] = equipment_list.filter(
            status='AVAILABLE').count()
        context['assigned_count'] = equipment_list.filter(
            status='ASSIGNED').count()
        context['repairing_count'] = equipment_list.filter(
            status='REPAIRING').count()
        context['damaged_count'] = equipment_list.filter(
            status='DAMAGED').count()
        return context


class BrandCreateView(LoginRequiredMixin, ITAdminRequiredMixin, SuccessMessageMixin, CreateView):
    model = Brand
    form_class = BrandForm
    template_name = 'equipment/brand_form.html'
    success_url = reverse_lazy('equipment:brand_list')
    success_message = "Brand has been created successfully!"


class BrandUpdateView(LoginRequiredMixin, ITAdminRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Brand
    form_class = BrandForm
    template_name = 'equipment/brand_form.html'
    success_url = reverse_lazy('equipment:brand_list')
    success_message = "Brand has been updated successfully!"


class BrandDeleteView(LoginRequiredMixin, ITAdminRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Brand
    template_name = 'equipment/brand_confirm_delete.html'
    success_url = reverse_lazy('equipment:brand_list')
    success_message = "Brand has been deleted successfully!"


# Category Views
class CategoryListView(LoginRequiredMixin, ITAdminRequiredMixin, ListView):
    model = Category
    template_name = 'equipment/category_list.html'
    context_object_name = 'categories'
    paginate_by = 10


class CategoryDetailView(LoginRequiredMixin, ITAdminRequiredMixin, DetailView):
    model = Category
    template_name = 'equipment/category_detail.html'
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.object
        equipment_list = Equipment.objects.filter(category=category)
        context['equipment_list'] = equipment_list
        context['available_count'] = equipment_list.filter(
            status='AVAILABLE').count()
        context['assigned_count'] = equipment_list.filter(
            status='ASSIGNED').count()
        context['repairing_count'] = equipment_list.filter(
            status='REPAIRING').count()
        context['damaged_count'] = equipment_list.filter(
            status='DAMAGED').count()
        return context


class CategoryCreateView(LoginRequiredMixin, ITAdminRequiredMixin, SuccessMessageMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'equipment/category_form.html'
    success_url = reverse_lazy('equipment:category_list')
    success_message = "Category has been created successfully!"


class CategoryUpdateView(LoginRequiredMixin, ITAdminRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'equipment/category_form.html'
    success_url = reverse_lazy('equipment:category_list')
    success_message = "Category has been updated successfully!"


class CategoryDeleteView(LoginRequiredMixin, ITAdminRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Category
    template_name = 'equipment/category_confirm_delete.html'
    success_url = reverse_lazy('equipment:category_list')
    success_message = "Category has been deleted successfully!"


# --- DASHBOARD VIEW (WITH FIX) ---


class DashboardReportView(LoginRequiredMixin, ITAdminRequiredMixin, TemplateView):
    template_name = 'dashboard/reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request

        # Filter parameters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        category_id = request.GET.get('category')
        brand_id = request.GET.get('brand')
        status_filter = request.GET.get('status')

        # Base querysets
        eq_query = Equipment.objects.all()
        req_query = Request.objects.all()
        maint_query = MaintenanceRecord.objects.all()

        # Date helper
        def parse_date(date_str):
            try:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                return None

        start = parse_date(start_date)
        end = parse_date(end_date)

        if start:
            eq_query = eq_query.filter(purchase_date__gte=start)
            req_query = req_query.filter(created_at__date__gte=start)
            maint_query = maint_query.filter(sent_date__gte=start)
        if end:
            eq_query = eq_query.filter(purchase_date__lte=end)
            req_query = req_query.filter(created_at__date__lte=end)
            maint_query = maint_query.filter(sent_date__lte=end)

        if category_id:
            eq_query = eq_query.filter(category_id=category_id)
        if brand_id:
            eq_query = eq_query.filter(brand_id=brand_id)
        if status_filter:
            eq_query = eq_query.filter(status=status_filter)

        # Aggregate equipment statistics with proper type casting
        status_stats = eq_query.aggregate(
            total=Count('id'),
            available=Count('id', filter=Q(status='AVAILABLE')),
            assigned=Count('id', filter=Q(status='ASSIGNED')),
            repairing=Count('id', filter=Q(status='REPAIRING')),
            damaged=Count('id', filter=Q(status='DAMAGED')),
            total_value=Coalesce(
                Sum('purchase_cost'),
                Decimal('0.00'),
                output_field=DecimalField()
            )
        )

        # Analytics queries
        cat_qs = eq_query.values('category__name').annotate(
            count=Count('id')).order_by('-count')
        brand_qs = eq_query.values('brand__name').annotate(
            count=Count('id')).order_by('-count')
        cost_qs = eq_query.annotate(month=TruncMonth('purchase_date')).values(
            'month').annotate(total=Sum('purchase_cost')).order_by('month')
        trends_qs = req_query.annotate(month=TruncMonth('created_at')).values(
            'month').annotate(count=Count('id')).order_by('month')
        prio_data = req_query.values('priority').annotate(
            count=Count('id')).order_by('-count')

        vendor_qs = MaintenanceRecord.objects.filter(equipment__in=eq_query).values(
            'vendor__name').annotate(repair_count=Count('id')).order_by('-repair_count')
        maint_qs = maint_query.annotate(month=TruncMonth('sent_date')).values(
            'month').annotate(total_cost=Sum('actual_cost')).order_by('month')
        dept_query = req_query.values('user__department__name').annotate(
            count=Count('id')).order_by('-count')

        analytics_data = {
            'health': {
                'labels': ['Available', 'Assigned', 'Repairing', 'Damaged'],
                'series': [
                    status_stats.get('available', 0),
                    status_stats.get('assigned', 0),
                    status_stats.get('repairing', 0),
                    status_stats.get('damaged', 0)
                ]
            },
            'categories': {
                'labels': [c['category__name'] or "Uncategorized" for c in cat_qs],
                'series': [c['count'] for c in cat_qs]
            },
            'brands': {
                'labels': [b['brand__name'] or "Unknown" for b in brand_qs],
                'series': [b['count'] for b in brand_qs]
            },
            'costs': {
                'labels': [m['month'].strftime('%b %Y') for m in cost_qs if m['month']],
                'series': [float(m['total'] or 0) for m in cost_qs]
            },
            'trends': {
                'labels': [m['month'].strftime('%b %Y') for m in trends_qs if m['month']],
                'series': [m['count'] for m in trends_qs]
            },
            'priority': {
                'labels': [p['priority'] for p in prio_data],
                'series': [p['count'] for p in prio_data]
            },
            'vendors': {
                'labels': [v['vendor__name'] or "Internal" for v in vendor_qs],
                'series': [v['repair_count'] for v in vendor_qs]
            },
            'maintenance': {
                'labels': [m['month'].strftime('%b %Y') for m in maint_qs if m['month']],
                'series': [float(m['total_cost'] or 0) for m in maint_qs]
            },
            'departments': {
                'labels': [d['user__department__name'] for d in dept_query if d['user__department__name']],
                'series': [d['count'] for d in dept_query if d['user__department__name']]
            }
        }

        context.update({
            'total_equipment': status_stats.get('total', 0),
            'available_equipment': status_stats.get('available', 0),
            'assigned_equipment': status_stats.get('assigned', 0),
            'repairing_equipment': status_stats.get('repairing', 0),
            'total_value': status_stats.get('total_value', 0),
            'analytics_json': json.dumps(analytics_data),
            'categories': Category.objects.all(),
            'brands': Brand.objects.all(),
            'status_choices': Equipment.STATUS_CHOICES,
            'departments': Department.objects.all(),
            'filter_start_date': start_date or '',
            'filter_end_date': end_date or '',
            'filter_category': category_id or '',
            'filter_brand': brand_id or '',
            'filter_status': status_filter or '',
        })
        return context


class ComprehensiveReportView(LoginRequiredMixin, ITAdminRequiredMixin, TemplateView):
    template_name = 'reports/comprehensive.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request

        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        category = request.GET.get('category')
        brand = request.GET.get('brand')
        status = request.GET.get('status')

        eq_query = Equipment.objects.all()

        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                eq_query = eq_query.filter(purchase_date__gte=start)
            except (ValueError, TypeError):
                pass

        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                eq_query = eq_query.filter(purchase_date__lte=end)
            except (ValueError, TypeError):
                pass

        if category:
            eq_query = eq_query.filter(category_id=category)

        if brand:
            eq_query = eq_query.filter(brand_id=brand)

        if status:
            eq_query = eq_query.filter(status=status)

        from django.db.models.functions import ExtractDay
        from django.db.models import F, ExpressionWrapper, DateField, IntegerField

        today = utc_now().date()

        # Optimize with annotations instead of Python loop
        equipment_list = eq_query.select_related(
            'brand', 'category', 'original_vendor', 'current_repair_vendor', 'assigned_to', 'assigned_to__department'
        ).annotate(
            days_owned=ExpressionWrapper(
                utc_now().date() - F('purchase_date'),
                output_field=IntegerField()
            ),
            warranty_days_left=ExpressionWrapper(
                F('warranty_expiry') - utc_now().date(),
                output_field=IntegerField()
            )
        )

        # Pre-fetch assignments to avoid N+1 and complex dictionary building
        from requests.models import Assignment
        assignments = Assignment.objects.filter(
            equipment__in=eq_query
        ).select_related('user', 'user__department')

        assignment_map = {a.equipment_id: a for a in assignments}

        enriched_equipment = []
        for eq in equipment_list[:1000]:
            assign = assignment_map.get(eq.id)

            days_assigned = (
                today - assign.assigned_date).days if assign and assign.assigned_date else None

            warranty_status = 'EXPIRED'
            if eq.warranty_expiry:
                w_days = (eq.warranty_expiry - today).days
                warranty_status = 'EXPIRED' if w_days < 0 else (
                    'EXPIRING SOON' if w_days <= 30 else 'ACTIVE')

            age_years, age_months, age_days = 0, 0, 0
            if eq.purchase_date:
                delta_years = today.year - eq.purchase_date.year
                delta_months = today.month - eq.purchase_date.month
                delta_days = today.day - eq.purchase_date.day
                if delta_days < 0:
                    delta_months -= 1
                    prev_month = today.replace(day=1) - timedelta(days=1)
                    delta_days += prev_month.day
                if delta_months < 0:
                    delta_years -= 1
                    delta_months += 12
                age_years, age_months, age_days = delta_years, delta_months, delta_days

            warranty_years, warranty_months, warranty_days = 0, 0, 0
            if eq.warranty_expiry:
                w_target = eq.warranty_expiry
                if w_target >= today:
                    delta_years = w_target.year - today.year
                    delta_months = w_target.month - today.month
                    delta_days = w_target.day - today.day
                    if delta_days < 0:
                        delta_months -= 1
                        prev_month = today.replace(day=1) - timedelta(days=1)
                        delta_days += prev_month.day
                    if delta_months < 0:
                        delta_years -= 1
                        delta_months += 12
                    warranty_years, warranty_months, warranty_days = delta_years, delta_months, delta_days

            enriched_equipment.append({
                'obj': eq,
                'days_owned': eq.days_owned,
                'warranty_days_left': eq.warranty_days_left,
                'age_years': age_years,
                'age_months': age_months,
                'age_days': age_days,
                'warranty_years': warranty_years,
                'warranty_months': warranty_months,
                'warranty_days': warranty_days,
                'warranty_status': warranty_status,
                'assigned_to': assign.user if assign else None,
                'department': assign.user.department if assign and assign.user else None,
                'days_assigned': days_assigned,
            })

        total_eq = eq_query.count()
        total_val = eq_query.aggregate(
            total=Sum('purchase_cost'))['total'] or 0
        avg_cost = total_val / total_eq if total_eq > 0 else 0

        context.update({
            'total_equipment': total_eq,
            'available_equipment': eq_query.filter(status='AVAILABLE').count(),
            'assigned_equipment': eq_query.filter(status='ASSIGNED').count(),
            'repairing_equipment': eq_query.filter(status='REPAIRING').count(),
            'damaged_equipment': eq_query.filter(status='DAMAGED').count(),
            'total_value': total_val,
            'avg_cost': avg_cost,
            'categories': Category.objects.all(),
            'brands': Brand.objects.all(),
            'status_choices': Equipment.STATUS_CHOICES,
            'filter_start_date': start_date or '',
            'filter_end_date': end_date or '',
            'filter_category': category or '',
            'filter_brand': brand or '',
            'filter_status': status or '',
            'filtered_equipment': enriched_equipment,
        })
        return context


class MaintenanceHistoryReportView(LoginRequiredMixin, ITAdminRequiredMixin, TemplateView):
    template_name = 'reports/maintenance_history.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request

        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        vendor_id = request.GET.get('vendor')
        status_filter = request.GET.get('status')

        from equipment.models import MaintenanceRecord
        from requests.models import Request

        maint_query = MaintenanceRecord.objects.select_related(
            'equipment', 'equipment__brand', 'vendor', 'request', 'request__user'
        )

        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                maint_query = maint_query.filter(sent_date__gte=start)
            except (ValueError, TypeError):
                pass

        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                maint_query = maint_query.filter(sent_date__lte=end)
            except (ValueError, TypeError):
                pass

        if vendor_id:
            maint_query = maint_query.filter(vendor_id=vendor_id)

        if status_filter:
            maint_query = maint_query.filter(status=status_filter)

        records = []
        for m in maint_query[:200]:
            repair_duration = None
            if m.sent_date and m.actual_return_date:
                repair_duration = (m.actual_return_date - m.sent_date).days
            elif m.sent_date and m.expected_return_date:
                repair_duration = (m.expected_return_date - m.sent_date).days

            cost_diff = float(m.actual_cost or 0) - \
                float(m.estimated_cost or 0) if m.actual_cost else None

            records.append({
                'equipment': f"{m.equipment.brand.name} {m.equipment.model_number}",
                'tracking_id': m.equipment.tracking_id,
                'serial_number': m.equipment.serial_number,
                'vendor': m.vendor.name if m.vendor else 'Internal',
                'issue': m.issue_description,
                'sent_date': m.sent_date,
                'expected_return': m.expected_return_date,
                'actual_return': m.actual_return_date,
                'repair_duration': repair_duration,
                'estimated_cost': float(m.estimated_cost or 0),
                'actual_cost': float(m.actual_cost) if m.actual_cost else None,
                'cost_diff': cost_diff,
                'status': m.status,
                'request_by': m.request.user.get_full_name() if m.request and m.request.user else '-',
            })

        total_estimated = sum(r['estimated_cost'] for r in records)
        total_actual = sum(r['actual_cost']
                           for r in records if r['actual_cost'])
        total_records = maint_query.count()
        completed_records = maint_query.filter(status='COMPLETED').count()

        duration_items = [r for r in records if r['repair_duration']]
        avg_duration = sum(r['repair_duration'] for r in duration_items) / \
            len(duration_items) if duration_items else 0

        context.update({
            'records': records,
            'vendors': Vendor.objects.all(),
            'total_records': total_records,
            'completed_records': completed_records,
            'total_estimated': total_estimated,
            'total_actual': total_actual,
            'avg_duration': round(avg_duration, 1) if avg_duration else 0,
            'filter_start_date': start_date or '',
            'filter_end_date': end_date or '',
            'filter_vendor': vendor_id or '',
            'filter_status': status_filter or '',
        })
        return context


class RequestSummaryReportView(LoginRequiredMixin, ITAdminRequiredMixin, TemplateView):
    template_name = 'reports/request_summary.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request

        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        priority = request.GET.get('priority')
        req_status = request.GET.get('status')

        from requests.models import Request

        req_query = Request.objects.select_related(
            'user', 'user__department').prefetch_related('logs')

        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                req_query = req_query.filter(created_at__date__gte=start)
            except (ValueError, TypeError):
                pass

        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                req_query = req_query.filter(created_at__date__lte=end)
            except (ValueError, TypeError):
                pass

        if priority:
            req_query = req_query.filter(priority=priority)

        if req_status:
            req_query = req_query.filter(status=req_status)

        from django.utils.timezone import now as utc_now
        today = utc_now().date()

        requests_data = []
        for r in req_query[:200]:
            days_open = (today - r.created_at.date()
                         ).days if r.created_at else 0

            logs = r.logs.all().order_by('timestamp') if hasattr(r, 'logs') else []
            timeline = [{'action': 'Created', 'timestamp': r.created_at,
                         'by': r.user.get_full_name() or r.user.username}]
            for log in logs[:10]:
                timeline.append({
                    'action': f"{log.old_status} -> {log.new_status}",
                    'timestamp': log.timestamp,
                    'by': log.action_by.get_full_name() if log.action_by else 'System',
                })

            requests_data.append({
                'id': str(r.id),
                'tracking_id': f"REQ-{r.created_at.year}-{str(r.id)[:8].upper()}",
                'request_type': r.get_request_type_display() if hasattr(r, 'get_request_type_display') else r.request_type,
                'priority': r.priority,
                'priority_display': r.get_priority_display() if hasattr(r, 'get_priority_display') else r.priority,
                'status': r.status,
                'status_display': r.get_status_display(),
                'user': r.user.get_full_name() or r.user.username,
                'department': r.user.department.name if r.user.department else '-',
                'created_at': r.created_at,
                'days_open': days_open,
                'reason': r.reason[:100] if r.reason else '',
                'timeline': timeline,
            })

        context.update({
            'requests': requests_data,
            'total_requests': req_query.count(),
            'pending_requests': req_query.filter(status='PENDING').count(),
            'approved_requests': req_query.filter(status__in=['MANAGER_APPROVED', 'IT_APPROVED']).count(),
            'completed_requests': req_query.filter(status='COMPLETED').count(),
            'rejected_requests': req_query.filter(status='REJECTED').count(),
            'filter_start_date': start_date or '',
            'filter_end_date': end_date or '',
            'filter_priority': priority or '',
            'filter_status': req_status or '',
            'priority_choices': Request._meta.get_field('priority').choices if hasattr(Request, '_meta') else [],
            'status_choices': Request._meta.get_field('status').choices if hasattr(Request, '_meta') else [],
        })
        return context


class VendorPerformanceReportView(LoginRequiredMixin, ITAdminRequiredMixin, TemplateView):
    template_name = 'reports/vendor_performance.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request

        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        from equipment.models import MaintenanceRecord

        maint_query = MaintenanceRecord.objects.filter(
            vendor__isnull=False).select_related('vendor', 'equipment')

        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                maint_query = maint_query.filter(sent_date__gte=start)
            except (ValueError, TypeError):
                pass

        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                maint_query = maint_query.filter(sent_date__lte=end)
            except (ValueError, TypeError):
                pass

        vendor_stats = []
        for vendor in Vendor.objects.all():
            v_records = maint_query.filter(vendor=vendor)
            total = v_records.count()
            if total == 0:
                continue

            completed = v_records.filter(status='COMPLETED').count()
            in_progress = v_records.filter(status='IN_PROGRESS').count()

            estimated = sum(float(r.estimated_cost or 0) for r in v_records)
            actual = sum(float(r.actual_cost or 0)
                         for r in v_records if r.actual_cost)

            avg_cost_diff = ((actual - estimated) /
                             estimated * 100) if estimated > 0 else 0

            durations = []
            for r in v_records.filter(status='COMPLETED', actual_return_date__isnull=False, sent_date__isnull=False):
                dur = (r.actual_return_date - r.sent_date).days
                if dur > 0:
                    durations.append(dur)

            avg_duration = sum(durations) / len(durations) if durations else 0
            on_time = sum(1 for r in v_records.filter(status='COMPLETED')
                          if r.actual_return_date and r.expected_return_date and r.actual_return_date <= r.expected_return_date)
            on_time_rate = (on_time / completed * 100) if completed > 0 else 0

            vendor_stats.append({
                'vendor': vendor,
                'total_jobs': total,
                'completed': completed,
                'in_progress': in_progress,
                'completion_rate': round(completed / total * 100, 1),
                'total_estimated': estimated,
                'total_actual': actual,
                'avg_cost_diff': round(avg_cost_diff, 1),
                'avg_duration': round(avg_duration, 1),
                'on_time_rate': round(on_time_rate, 1),
            })

        vendor_stats.sort(key=lambda x: x['total_jobs'], reverse=True)

        context.update({
            'vendor_stats': vendor_stats,
            'total_vendors': len(vendor_stats),
            'filter_start_date': start_date or '',
            'filter_end_date': end_date or '',
        })
        return context


class DepartmentDistributionReportView(LoginRequiredMixin, ITAdminRequiredMixin, TemplateView):
    template_name = 'reports/department_distribution.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request

        from accounts.models import Department
        from requests.models import Assignment

        dept_data = []
        for dept in Department.objects.all():
            users = dept.user_set.all()
            total_users = users.count()

            # Use assigned_date__isnull instead of returned_date
            # Since returned_date was removed, we check for active assignments
            assigned = Assignment.objects.filter(
                user__in=users
            ).count()

            equipment_count = Equipment.objects.filter(
                assigned_to__in=users
            ).count()

            total_value = Equipment.objects.filter(
                assigned_to__in=users
            ).aggregate(total=Sum('purchase_cost'))['total'] or 0

            dept_data.append({
                'department': dept,
                'total_users': total_users,
                'assigned_count': assigned,
                'equipment_count': equipment_count,
                'total_value': float(total_value),
                'avg_per_user': round(equipment_count / total_users, 1) if total_users > 0 else 0,
            })

        dept_data.sort(key=lambda x: x['equipment_count'], reverse=True)

        total_equipment = sum(d['equipment_count'] for d in dept_data)
        total_value = sum(d['total_value'] for d in dept_data)
        total_users = sum(d['total_users'] for d in dept_data)

        dept_labels = [d['department'].name for d in dept_data]
        dept_values = [d['assigned_count'] for d in dept_data]

        dept_labels_json = json.dumps(
            dept_labels) if dept_labels else json.dumps([])
        dept_values_json = json.dumps(
            dept_values) if dept_values else json.dumps([])

        context.update({
            'departments': dept_data,
            'total_equipment': total_equipment,
            'total_value': total_value,
            'total_users': total_users,
            'total_departments': len(dept_data),
            'dept_labels_json': dept_labels_json,
            'dept_values_json': dept_values_json,
        })
        return context
        return context


class RequestTurnaroundReportView(LoginRequiredMixin, ITAdminRequiredMixin, TemplateView):
    template_name = 'reports/request_turnaround.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request

        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        priority = request.GET.get('priority')

        from requests.models import Request

        req_query = Request.objects.all()

        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                req_query = req_query.filter(created_at__date__gte=start)
            except (ValueError, TypeError):
                pass

        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                req_query = req_query.filter(created_at__date__lte=end)
            except (ValueError, TypeError):
                pass

        if priority:
            req_query = req_query.filter(priority=priority)

        from django.utils.timezone import now as utc_now
        today = utc_now()

        turnaround_data = []
        for r in req_query[:300]:
            completed_log = r.logs.filter(
                new_status='COMPLETED').order_by('timestamp').first()
            if completed_log:
                total_hours = (completed_log.timestamp -
                               r.created_at).total_seconds() / 3600
                total_days = round(total_hours / 24, 1)
            else:
                total_hours = (today - r.created_at).total_seconds() / 3600
                total_days = round(total_hours / 24, 1)

            manager_approval_time = None
            it_approval_time = None
            delivery_time = None

            if hasattr(r, 'logs'):
                logs = r.logs.all().order_by('timestamp')
                prev_log = None
                for log in logs:
                    if prev_log:
                        hours = (log.timestamp -
                                 prev_log.timestamp).total_seconds() / 3600
                        if 'MANAGER_APPROVED' in log.new_status and 'MANAGER' not in str(prev_log.new_status):
                            manager_approval_time = round(hours, 1)
                        elif 'IT_RECEIVED' in log.new_status or 'COMPLETED' in log.new_status:
                            if 'MANAGER' in str(prev_log.new_status):
                                it_approval_time = round(hours, 1)
                                delivery_time = round(
                                    (log.timestamp - prev_log.timestamp).total_seconds() / 3600, 1)
                    prev_log = log

            turnaround_data.append({
                'id': str(r.id),
                'tracking_id': f"REQ-{r.created_at.year}-{str(r.id)[:8].upper()}",
                'request_type': r.get_request_type_display() if hasattr(r, 'get_request_type_display') else r.request_type,
                'priority': r.priority,
                'priority_display': r.get_priority_display() if hasattr(r, 'get_priority_display') else r.priority,
                'status': r.status,
                'status_display': r.get_status_display(),
                'user': r.user.get_full_name() or r.user.username,
                'created_at': r.created_at,
                'completed_at': completed_log.timestamp if completed_log and completed_log.timestamp else None,
                'total_days': total_days,
                'manager_time': manager_approval_time,
                'it_time': it_approval_time,
                'delivery_time': delivery_time,
            })

        turnaround_data.sort(key=lambda x: x['total_days'], reverse=True)

        if turnaround_data:
            manager_items = [r for r in turnaround_data if r['manager_time']]
            it_items = [r for r in turnaround_data if r['it_time']]

            avg_turnaround = sum(r['total_days']
                                 for r in turnaround_data) / len(turnaround_data)
            avg_manager_time = sum(
                r['manager_time'] for r in manager_items) / len(manager_items) if manager_items else 0
            avg_it_time = sum(r['it_time'] for r in it_items) / \
                len(it_items) if it_items else 0
        else:
            avg_turnaround = avg_manager_time = avg_it_time = 0

        context.update({
            'turnaround_data': turnaround_data,
            'total_requests': req_query.count(),
            'completed_requests': req_query.filter(status='COMPLETED').count(),
            'avg_turnaround': round(avg_turnaround, 1),
            'avg_manager_time': round(avg_manager_time, 1),
            'avg_it_time': round(avg_it_time, 1),
            'filter_start_date': start_date or '',
            'filter_end_date': end_date or '',
            'filter_priority': priority or '',
        })
        return context
