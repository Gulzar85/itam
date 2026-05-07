import logging
from typing import Any, cast

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, ListView
from django.db.models import Count
from services.permissions import ITAdminRequiredMixin, ManagerOrAdminRequiredMixin

from accounts.models import User
from equipment.models import Equipment, EquipmentLog, MaintenanceRecord, Vendor

from .forms import ITRequestForm
from .models import Assignment, Request, RequestLog
from services.request_service import RequestService
from services.request_workflow import can_actor_transition, get_valid_statuses

logger = logging.getLogger(__name__)


class MyEquipmentView(LoginRequiredMixin, ListView):
    """Shows equipment assigned to the current user, regardless of role."""
    model = Equipment
    template_name = 'requests/my_equipment.html'
    context_object_name = 'equipment_list'
    paginate_by = 12

    def get_queryset(self):
        user = cast(User, self.request.user)
        return Equipment.objects.select_related(
            'brand', 'category', 'assigned_to'
        ).filter(assigned_to=user).order_by('-assigned_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['total_assigned'] = self.get_queryset().count()
        context['today'] = timezone.now().date()
        context['warranty_expiring'] = self.get_queryset().filter(
            warranty_expiry__isnull=False,
            warranty_expiry__lt=timezone.now().date() + timezone.timedelta(days=30)
        ).count()
        return context


class RequestDashboardView(LoginRequiredMixin, ListView):
    """
    Central hub for tracking IT requests with role-based visibility.
    """
    model = Request
    template_name = 'dashboard/index.html'
    context_object_name = 'requests'
    paginate_by = 10

    def get_queryset(self):
        user = cast(User, self.request.user)
        # Optimized with select_related to prevent N+1 query issues
        base_qs = Request.objects.select_related(
            'user', 'equipment', 'category_needed', 'user__manager'
        )

        if hasattr(user, 'role') and user.role == 'IT_ADMIN':
            return base_qs.all().order_by('-created_at')

        # Hierarchy View: Show user's requests and those they need to approve[cite: 19]
        if hasattr(user, 'role') and (user.role == 'IT_ADMIN' or getattr(user, 'can_approve', False)):
            return base_qs.filter(Q(user=user) | Q(user__manager=user)).distinct().order_by('-created_at')

        return base_qs.filter(user=user).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        # Single-hit aggregation for dashboard performance[cite: 18, 19]
        context['stats'] = qs.aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status='PENDING')),
            in_progress=Count('id', filter=Q(status='IN_PROGRESS')),
            completed=Count('id', filter=Q(status='COMPLETED')),
        )
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
        
        # If user has no manager, skip manager approval and set status to MANAGER_APPROVED
        if not self.request.user.manager:
            obj.status = 'MANAGER_APPROVED'
            messages.success(self.request, "Request submitted. No manager assigned - sent directly to IT Admin.")
        else:
            obj.status = 'PENDING'
        
        response = super().form_valid(form)
        
        # Create appropriate log entry
        from requests.models import RequestLog
        if not self.request.user.manager:
            RequestLog.objects.create(
                request=obj,
                action_by=self.request.user,
                old_status='PENDING',
                new_status='MANAGER_APPROVED',
                remarks="No manager assigned. Auto-approved for IT Admin review."
            )
        else:
            RequestLog.objects.create(
                request=obj,
                action_by=self.request.user,
                old_status='NONE',
                new_status='PENDING',
                remarks="Request submitted and awaiting manager approval."
            )
            
        return response


class RequestActionView(LoginRequiredMixin, View):
    def post(self, request, pk):
        request_obj = get_object_or_404(Request, pk=pk)
        new_status = request.POST.get('status')
        # Ensure remarks is never None to avoid IntegrityError in RequestLog
        remarks = request.POST.get(
            'remarks') or f"Status updated to {new_status} via Dashboard"

        user = cast(User, request.user)

        if not new_status:
            return JsonResponse({'status': 'error', 'message': 'New status is required'}, status=400)

        valid_statuses = get_valid_statuses()
        if new_status not in valid_statuses:
            return JsonResponse({'status': 'error', 'message': 'Invalid status'}, status=400)

        if not can_actor_transition(user, request_obj, new_status):
            return JsonResponse({
                'status': 'error',
                'message': 'You are not allowed to apply this transition.'
            }, status=403)

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
            return JsonResponse({'status': 'error', 'message': 'Unable to update request status.'}, status=500)


class RequestDetailView(LoginRequiredMixin, DetailView):
    model = Request
    template_name = 'requests/request_detail.html'
    context_object_name = 'req'

    def get_queryset(self):
        user = cast(User, self.request.user)
        queryset = Request.objects.select_related(
            'user', 'equipment', 'category_needed', 'brand_preference', 'user__manager'
        )

        if user.role == 'IT_ADMIN' or user.is_staff:
            return queryset
        if getattr(user, 'can_approve', False):
            return queryset.filter(Q(user=user) | Q(user__manager=user)).distinct()
        return queryset.filter(user=user)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        req_obj = self.get_object()
        user = cast(User, self.request.user)

        # Get logs - sort by timestamp ascending for chronological order
        logs = list(req_obj.logs.all().order_by('timestamp'))
        
        # Create virtual "created" log entry at the start
        created_log = type('obj', (object,), {
            'timestamp': req_obj.created_at,
            'action_by': req_obj.user,
            'status': 'CREATED',
            'new_status': 'PENDING',
            'remarks': f'Request created by {req_obj.user.get_full_name() or req_obj.user.username}'
        })()
        
        # Add created event at the start
        logs.insert(0, created_log)
        
        context['logs'] = logs
        context['available_assets'] = Equipment.objects.filter(
            status='AVAILABLE').select_related('brand', 'category')
        context['vendors'] = Vendor.objects.all().order_by('name')

        # Permission Logic
        context['can_perform_actions'] = (
            user.is_staff or
            (hasattr(user, 'role') and user.role in ['IT_ADMIN'] or getattr(user, 'can_approve', False))
        )
        return context


class AssignmentCreateView(LoginRequiredMixin, ITAdminRequiredMixin, SuccessMessageMixin, CreateView):
    """General assignment view (not linked to a specific request)"""
    model = Assignment
    fields = ['equipment', 'user', 'notes']
    template_name = 'requests/assignment_form.html'
    success_url = reverse_lazy('equipment:equipment_list')
    success_message = "Asset successfully assigned."

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


class RequestAssignmentView(LoginRequiredMixin, ITAdminRequiredMixin, View):

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
            logger.error(f"Request assignment failed for {pk}: {str(e)}")
            return JsonResponse({'status': 'error', 'message': 'Unable to assign equipment.'}, status=500)


class ManagerApprovalView(LoginRequiredMixin, ManagerOrAdminRequiredMixin, ListView):
    """View for managers/admins to approve or reject team requests"""
    model = Request
    template_name = 'requests/manager_approvals.html'
    context_object_name = 'requests'
    paginate_by = 20

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


class ProcessMaintenanceView(LoginRequiredMixin, ITAdminRequiredMixin, View):
    """
    IT Admin ke liye: Asset ko repair ke liye vendor ke paas bhejne ka logic.
    """

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

            # Check if maintenance record already exists
            m_record = MaintenanceRecord.objects.filter(request=request_obj).first()
            
            if m_record:
                # Update existing record
                m_record.vendor = vendor
                m_record.estimated_cost = est_cost
                m_record.expected_return_date = return_date if return_date else None
                m_record.status = 'IN_PROGRESS'
                m_record.save()
            else:
                # Create new record
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
            return JsonResponse({'status': 'error', 'message': 'Unable to process maintenance request.'}, status=500)


class CompleteMaintenanceView(LoginRequiredMixin, ITAdminRequiredMixin, View):
    """Repair se wapas receive karna aur usi employee ko assigned rakhna"""

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
                m_record.status = 'COMPLETED'
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
            return JsonResponse({'status': 'error', 'message': 'Unable to complete maintenance.'}, status=400)
