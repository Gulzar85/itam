from equipment.models import Equipment, Category, Brand, Vendor, MaintenanceRecord
from django.db.models.functions import TruncMonth, Coalesce
from django.db.models import Sum, Count
from django.views.generic import TemplateView
from django.db.models import Sum, Count, Q
import json
from datetime import datetime, timedelta
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.timezone import now
from requests.models import Request
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from requests.models import Request
from requests.utils import get_advanced_dashboard_stats

from .forms import BrandForm, CategoryForm, EquipmentForm, VendorForm
from .models import (
    Brand,
    Category,
    Equipment,
    EquipmentLog,
    MaintenanceRecord,
    Vendor,
)


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
            queryset = queryset.filter(
                Q(serial_number__icontains=search) |
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
        context['logs'] = self.object.logs.all().order_by('-timestamp')
        from requests.models import Assignment
        context['current_assignment'] = Assignment.objects.filter(
            equipment=self.object,
            returned_date__isnull=True
        ).first()
        return context


class EquipmentCreateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, CreateView):
    """Create new equipment"""
    model = Equipment
    form_class = EquipmentForm
    template_name = 'equipment/equipment_form.html'
    success_url = reverse_lazy('equipment:equipment_list')
    success_message = "Equipment has been created successfully!"

    def test_func(self):
        return self.request.user.role == 'IT_ADMIN'

    def form_valid(self, form):
        if not form.cleaned_data.get('status'):
            form.instance.status = 'AVAILABLE'
        return super().form_valid(form)


class EquipmentUpdateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    """Update existing equipment"""
    model = Equipment
    form_class = EquipmentForm
    template_name = 'equipment/equipment_form.html'
    success_url = reverse_lazy('equipment:equipment_list')
    success_message = "Equipment has been updated successfully!"

    def test_func(self):
        return self.request.user.role == 'IT_ADMIN'


class EquipmentDeleteView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView):
    """Delete equipment"""
    model = Equipment
    template_name = 'equipment/equipment_confirm_delete.html'
    success_url = reverse_lazy('equipment:equipment_list')
    success_message = "Equipment has been deleted successfully!"

    def test_func(self):
        return self.request.user.role == 'IT_ADMIN'


@method_decorator(csrf_exempt, name='dispatch')
class EquipmentStatusUpdateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """AJAX endpoint to update equipment status"""

    def test_func(self):
        return self.request.user.role == 'IT_ADMIN'

    def post(self, request, pk):
        equipment = get_object_or_404(Equipment, pk=pk)
        new_status = request.POST.get('status')

        if new_status in dict(Equipment.STATUS_CHOICES):
            old_status = equipment.status
            equipment.status = new_status
            equipment.save()

            EquipmentLog.objects.create(
                equipment=equipment,
                action_by=request.user,
                old_status=old_status,
                new_status=new_status,
                remarks=request.POST.get('remarks', 'Status updated')
            )

            return JsonResponse({'status': 'success', 'message': 'Status updated'})

        return JsonResponse({'status': 'error', 'message': 'Invalid status'}, status=400)


# Vendor Views
class VendorListView(LoginRequiredMixin, ListView):
    model = Vendor
    template_name = 'equipment/vendor_list.html'
    context_object_name = 'vendors'
    paginate_by = 10


class VendorDetailView(LoginRequiredMixin, DetailView):
    model = Vendor
    template_name = 'equipment/vendor_detail.html'
    context_object_name = 'vendor'


class VendorCreateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, CreateView):
    model = Vendor
    form_class = VendorForm
    template_name = 'equipment/vendor_form.html'
    success_url = reverse_lazy('equipment:vendor_list')
    success_message = "Vendor has been created successfully!"

    def test_func(self):
        return self.request.user.role == 'IT_ADMIN'


class VendorUpdateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = Vendor
    form_class = VendorForm
    template_name = 'equipment/vendor_form.html'
    success_url = reverse_lazy('equipment:vendor_list')
    success_message = "Vendor has been updated successfully!"

    def test_func(self):
        return self.request.user.role == 'IT_ADMIN'


class VendorDeleteView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView):
    model = Vendor
    template_name = 'equipment/vendor_confirm_delete.html'
    success_url = reverse_lazy('equipment:vendor_list')
    success_message = "Vendor has been deleted successfully!"

    def test_func(self):
        return self.request.user.role == 'IT_ADMIN'


# Brand Views
class BrandListView(LoginRequiredMixin, ListView):
    model = Brand
    template_name = 'equipment/brand_list.html'
    context_object_name = 'brands'
    paginate_by = 10


class BrandDetailView(LoginRequiredMixin, DetailView):
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


class BrandCreateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, CreateView):
    model = Brand
    form_class = BrandForm
    template_name = 'equipment/brand_form.html'
    success_url = reverse_lazy('equipment:brand_list')
    success_message = "Brand has been created successfully!"

    def test_func(self):
        return self.request.user.role == 'IT_ADMIN'


class BrandUpdateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = Brand
    form_class = BrandForm
    template_name = 'equipment/brand_form.html'
    success_url = reverse_lazy('equipment:brand_list')
    success_message = "Brand has been updated successfully!"

    def test_func(self):
        return self.request.user.role == 'IT_ADMIN'


class BrandDeleteView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView):
    model = Brand
    template_name = 'equipment/brand_confirm_delete.html'
    success_url = reverse_lazy('equipment:brand_list')
    success_message = "Brand has been deleted successfully!"

    def test_func(self):
        return self.request.user.role == 'IT_ADMIN'


# Category Views
class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'equipment/category_list.html'
    context_object_name = 'categories'
    paginate_by = 10


class CategoryDetailView(LoginRequiredMixin, DetailView):
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


class CategoryCreateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'equipment/category_form.html'
    success_url = reverse_lazy('equipment:category_list')
    success_message = "Category has been created successfully!"

    def test_func(self):
        return self.request.user.role == 'IT_ADMIN'


class CategoryUpdateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'equipment/category_form.html'
    success_url = reverse_lazy('equipment:category_list')
    success_message = "Category has been updated successfully!"

    def test_func(self):
        return self.request.user.role == 'IT_ADMIN'


class CategoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView):
    model = Category
    template_name = 'equipment/category_confirm_delete.html'
    success_url = reverse_lazy('equipment:category_list')
    success_message = "Category has been deleted successfully!"

    def test_func(self):
        return self.request.user.role == 'IT_ADMIN'


class DashboardReportView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'dashboard/reports.html'

    def test_func(self):
        return hasattr(self.request.user, 'role') and self.request.user.role == 'IT_ADMIN'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request

        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        category = request.GET.get('category')
        brand = request.GET.get('brand')
        status = request.GET.get('status')

        from datetime import datetime
        from django.utils.timezone import make_aware

        eq_query = Equipment.objects.all()
        req_query = Request.objects.all()
        maint_query = MaintenanceRecord.objects.all()

        if start_date:
            start = make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
            eq_query = eq_query.filter(purchase_date__gte=start)
            req_query = req_query.filter(created_at__gte=start)
            maint_query = maint_query.filter(sent_date__gte=start)

        if end_date:
            end = make_aware(datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59))
            eq_query = eq_query.filter(purchase_date__lte=end)
            req_query = req_query.filter(created_at__lte=end)
            maint_query = maint_query.filter(sent_date__lte=end)

        if category:
            eq_query = eq_query.filter(category_id=category)

        if brand:
            eq_query = eq_query.filter(brand_id=brand)

        if status:
            eq_query = eq_query.filter(status=status)

        total_eq = eq_query.count()
        total_val = eq_query.aggregate(total=Sum('purchase_cost'))['total'] or 0

        cat_qs = Category.objects.annotate(
            count=Count('equipments')).filter(
            equipments__in=eq_query).values('name').annotate(
            count=Count('id')).order_by('-count')[:5]
        if category:
            cat_qs = Category.objects.filter(id=category).annotate(count=Count('equipments'))

        brand_qs = Brand.objects.annotate(
            count=Count('equipments')).filter(
            equipments__in=eq_query).values('name').annotate(
            count=Count('id')).order_by('-count')[:5]
        if brand:
            brand_qs = Brand.objects.filter(id=brand).annotate(count=Count('equipments'))

        cost_qs = eq_query.exclude(purchase_date__isnull=True).annotate(
            month=TruncMonth('purchase_date')).values('month').annotate(total=Sum('purchase_cost')).order_by('month')

        trends_qs = req_query.annotate(month=TruncMonth('created_at')).values(
            'month').annotate(count=Count('id')).order_by('month')

        prio_data = req_query.values('priority').annotate(count=Count('id'))
        vendor_qs = Vendor.objects.annotate(repair_count=Count('repairing_items')).order_by('-repair_count')[:5]

        maint_qs = maint_query.exclude(sent_date__isnull=True).annotate(
            month=TruncMonth('sent_date')
        ).values('month').annotate(
            total_cost=Sum(Coalesce('actual_cost', 'estimated_cost'))
        ).order_by('month')

        analytics_data = {
            'health': {
                'labels': ['Available', 'Assigned', 'Repairing', 'Damaged'],
                'series': [
                    eq_query.filter(status='AVAILABLE').count(),
                    eq_query.filter(status='ASSIGNED').count(),
                    eq_query.filter(status='REPAIRING').count(),
                    eq_query.filter(status='DAMAGED').count()
                ]
            },
            'categories': {
                'labels': [c['name'] for c in cat_qs],
                'series': [c['count'] for c in cat_qs]
            },
            'costs': {
                'labels': [m['month'].strftime('%b %Y') for m in cost_qs if m['month']],
                'series': [float(m['total'] or 0) for m in cost_qs]
            },
            'trends': {
                'labels': [m['month'].strftime('%b %Y') for m in trends_qs if m['month']],
                'series': [m['count'] for m in trends_qs]
            },
            'brands': {
                'labels': [b['name'] for b in brand_qs],
                'series': [b['count'] for b in brand_qs]
            },
            'priority': {
                'labels': [p['priority'] for p in prio_data],
                'series': [p['count'] for p in prio_data]
            },
            'vendors': {
                'labels': list(vendor_qs.values_list('name', flat=True)),
                'series': list(vendor_qs.values_list('repair_count', flat=True))
            },
            'maintenance': {
                'labels': [m['month'].strftime('%b %Y') for m in maint_qs if m['month']],
                'series': [float(m['total_cost'] or 0) for m in maint_qs]
            }
        }

        context.update({
            'total_equipment': total_eq,
            'available_equipment': eq_query.filter(status='AVAILABLE').count(),
            'assigned_equipment': eq_query.filter(status='ASSIGNED').count(),
            'repairing_equipment': eq_query.filter(status='REPAIRING').count(),
            'total_value': total_val,
            'analytics_json': json.dumps(analytics_data),
            'categories': Category.objects.all(),
            'brands': Brand.objects.all(),
            'status_choices': Equipment.STATUS_CHOICES,
            'filter_start_date': start_date or '',
            'filter_end_date': end_date or '',
            'filter_category': category or '',
            'filter_brand': brand or '',
            'filter_status': status or '',
            'filtered_equipment': list(eq_query.select_related('brand', 'category')[:100]),
        })
        return context
