import logging
from typing import Any, cast

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, ListView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from accounts.models import User
from equipment.models import Equipment, EquipmentLog, MaintenanceRecord, Vendor

from .forms import ITRequestForm
from .models import Assignment, Request, RequestLog
from services.request_service import RequestService

logger = logging.getLogger(__name__)


class RequestDashboardView(LoginRequiredMixin, ListView):
    model = Request
    template_name = 'dashboard/index.html'
    context_object_name = 'requests'
    paginate_by = 10

    def get_queryset(self):
        user = cast(User, self.request.user)
        base_qs = Request.objects.select_related(
            'user', 'equipment', 'category_needed', 'user__manager'
        )

        if hasattr(user, 'role') and user.role == 'IT_ADMIN':
            return base_qs.all().order_by('-created_at')

        if hasattr(user, 'role') and user.role == 'MANAGER':
            return base_qs.filter(Q(user=user) | Q(user__manager=user)).distinct().order_by('-created_at')

        return base_qs.filter(user=user).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        context['stats'] = {
            'total': qs.count(),
            'pending': qs.filter(status='PENDING').count(),
            'in_progress': qs.filter(status='IN_PROGRESS').count(),
            'completed': qs.filter(status='COMPLETED').count(),
        }
        return context


class RequestCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Request
    form_class = ITRequestForm
    template_name = 'requests/request_form.html'
    success_url = reverse_lazy('dashboard')
    success_message = "Your IT request has been submitted successfully."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form: ITRequestForm):
        obj = cast(Request, form.instance)
        obj.user = cast(User, self.request.user)
        obj.status = 'PENDING'
        return super().form_valid(form)


@method_decorator(csrf_exempt, name='dispatch')
class RequestActionView(LoginRequiredMixin, View):
    def post(self, request, pk):
        request_obj = get_object_or_404(Request, pk=pk)
        new_status = request.POST.get('status')
        # Ensure remarks is never None to avoid IntegrityError in RequestLog
        remarks = request.POST.get(
            'remarks') or f"Status updated to {new_status} via Dashboard"

        user = cast(User, request.user)

        # Permission Logic
        is_manager = (request_obj.user.manager_id == user.id) if request_obj.user.manager else False
        is_it_admin = (hasattr(user, 'role') and user.role == 'IT_ADMIN')

        if not (is_manager or is_it_admin):
            return JsonResponse({'status': 'error', 'message': 'Permission Denied'}, status=403)

        if not new_status:
            return JsonResponse({'status': 'error', 'message': 'New status is required'}, status=400)

        try:
            # Service call handles the status change and log creation
            RequestService.update_request_status(
                request_obj=request_obj,
                new_status=new_status,
                action_by=user,
                remarks=remarks
            )

            return JsonResponse({
                'status': 'success',
                'new_status_display': request_obj.get_status_display(),
                'message': f'Request #{pk} updated successfully.'
            })
        except Exception as e:
            logger.error(f"Request status update failed for {pk}: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


class RequestDetailView(LoginRequiredMixin, DetailView):
    model = Request
    template_name = 'requests/request_detail.html'
    context_object_name = 'req'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        req_obj = self.get_object()
        user = cast(User, self.request.user)

        context['logs'] = req_obj.logs.all().order_by('-timestamp')
        context['available_assets'] = Equipment.objects.filter(
            status='AVAILABLE').select_related('brand', 'category')
        context['vendors'] = Vendor.objects.all().order_by('name')

        # Permission Logic
        context['can_perform_actions'] = (
            user.is_staff or
            (hasattr(user, 'role') and user.role in ['IT_ADMIN', 'MANAGER'])
        )
        return context


class AssignmentCreateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, CreateView):
    """General assignment view (not linked to a specific request)"""
    model = Assignment
    fields = ['equipment', 'user', 'notes']
    template_name = 'requests/assignment_form.html'
    success_url = reverse_lazy('equipment:equipment_list')
    success_message = "Asset successfully assigned."

    def test_func(self):
        return self.request.user.role == 'IT_ADMIN'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # 1. Dropdown Filter: Sirf AVAILABLE assets dikhayen
        form.fields['equipment'].queryset = Equipment.objects.filter(
            status='AVAILABLE')

        # 2. Styling (Optional): Dropdown ko behtar look denay ke liye label update karein
        form.fields[
            'equipment'].label_from_instance = lambda obj: f"{obj.category.name} | {obj.brand.name} {obj.model_number} (SN: {obj.serial_number})"

        # 3. Form control classes (Agar aap tailwind use kar rahe hain)
        for field_name, field in form.fields.items():
            field.widget.attrs.update({
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-blue-500 outline-none bg-white/50'
            })

        return form

    def form_valid(self, form):
        # Admin set karein jo laptop bhej raha hai
        form.instance.assigned_by = self.request.user

        # NOTE: Aapne bataya ke signals likhe hain,
        # isliye status auto-change ho jayega.
        return super().form_valid(form)


@method_decorator(csrf_exempt, name='dispatch')
class RequestAssignmentView(LoginRequiredMixin, UserPassesTestMixin, View):

    def test_func(self):
        return self.request.user.role == 'IT_ADMIN'

    def post(self, request, pk):
        request_obj = get_object_or_404(Request, pk=pk)
        equipment_id = request.POST.get('equipment_id')
        remarks = request.POST.get('remarks', 'Asset assigned by IT Admin')

        if not equipment_id:
            return JsonResponse({'status': 'error', 'message': 'Please select an asset.'}, status=400)

        try:
            # Asset hasil karein
            equipment = get_object_or_404(
                Equipment, id=equipment_id, status='AVAILABLE')

            # SERVICE CALL: Ye function RequestLog aur EquipmentLog dono banayega
            RequestService.update_request_status(
                request_obj=request_obj,
                new_status='COMPLETED',
                action_by=request.user,
                remarks=remarks,
                equipment_obj=equipment  # Pass the actual object
            )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


class ManagerApprovalView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """View for managers/admins to approve or reject team requests"""
    model = Request
    template_name = 'requests/manager_approvals.html'
    context_object_name = 'requests'
    paginate_by = 20

    def test_func(self):
        return self.request.user.role in ['IT_ADMIN', 'MANAGER']

    def get_queryset(self):
        user = self.request.user

        # 1. Global View for IT Admins
        if user.role == 'IT_ADMIN':
            return Request.objects.filter(status='PENDING').select_related(
                'user', 'equipment', 'category_needed', 'brand_preference'
            ).order_by('-created_at')

        # 2. Hierarchy View for Managers (and Employees who act as Managers)
        # Hum un users ki requests layenge jahan 'manager' field current user ke barabar hai
        return Request.objects.filter(
            user__manager=user,
            status='PENDING'
        ).select_related(
            'user', 'equipment', 'category_needed', 'brand_preference'
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Badge aur counters ke liye count bhej rahe hain
        context['pending_count'] = self.get_queryset().count()
        return context


@method_decorator(csrf_exempt, name='dispatch')
class ProcessMaintenanceView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    IT Admin ke liye: Asset ko repair ke liye vendor ke paas bhejne ka logic.
    """

    def test_func(self):
        return self.request.user.role == 'IT_ADMIN'

    @transaction.atomic
    def post(self, request, pk):
        request_obj = get_object_or_404(Request, pk=pk)

        vendor_id = request.POST.get('vendor_id')
        est_cost = request.POST.get('estimated_cost') or 0
        return_date = request.POST.get('expected_return_date')
        remarks = request.POST.get(
            'remarks') or "Sent to vendor for maintenance."

        if not vendor_id:
            return JsonResponse({'status': 'error', 'message': 'Vendor select karna zaroori hai.'}, status=400)

        try:
            vendor = get_object_or_404(Vendor, id=vendor_id)

            MaintenanceRecord.objects.create(
                request=request_obj,
                equipment=request_obj.equipment,
                vendor=vendor,
                estimated_cost=est_cost,
                expected_return_date=return_date if return_date else None,
            )

            RequestService.update_request_status(
                request_obj=request_obj,
                new_status='IN_PROGRESS',
                action_by=request.user,
                remarks=f"{remarks} (Vendor: {vendor.name}, Est Cost: {est_cost})"
            )

            return JsonResponse({
                'status': 'success',
                'message': 'Asset maintenance process shuru ho gaya hai.'
            })

        except Exception as e:
            logger.error(f"Maintenance process failed for {pk}: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class CompleteMaintenanceView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Repair se wapas receive karna aur usi employee ko assigned rakhna"""

    def test_func(self):
        return self.request.user.role == 'IT_ADMIN'

    @transaction.atomic
    def post(self, request, pk):
        request_obj = get_object_or_404(Request, pk=pk)
        actual_cost = request.POST.get('actual_cost')
        actual_date = request.POST.get('actual_return_date')
        notes = request.POST.get('repair_notes')

        try:
            m_record = MaintenanceRecord.objects.filter(
                request=request_obj,
                actual_return_date__isnull=True
            ).first()

            if m_record:
                m_record.actual_cost = actual_cost or 0
                m_record.actual_return_date = actual_date if actual_date else timezone.now().date()
                m_record.repair_notes = notes
                m_record.save()

            if request_obj.equipment:
                eq = request_obj.equipment
                old_eq_status = eq.status

                eq.status = 'ASSIGNED'
                eq.save()

                EquipmentLog.objects.create(
                    equipment=eq,
                    action_by=request.user,
                    old_status=old_eq_status,
                    new_status='ASSIGNED',
                    remarks=f"Repair completed. Asset returned to employee: {request_obj.user.get_full_name()}"
                )

            old_req_status = request_obj.status
            request_obj.status = 'COMPLETED'
            request_obj.save()

            RequestLog.objects.create(
                request=request_obj,
                action_by=request.user,
                old_status=old_req_status,
                new_status='COMPLETED',
                remarks=f"Repair finished. Cost: {actual_cost}. Asset handed back to user."
            )

            return JsonResponse({'status': 'success'})

        except Exception as e:
            logger.error(f"Complete maintenance failed for {pk}: {str(e)}")
            messages.success(
                request, "Maintenance record updated and asset returned to employee.")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
