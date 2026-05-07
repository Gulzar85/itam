import json

from django.db import models
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy

from accounts.models import User
from equipment.models import Equipment, Vendor, Brand, Category
from requests.models import Request
from .models import BusinessInfo, SocialMediaLink
from .forms.forms_backup import BusinessInfoForm, SocialMediaLinkForm


class BusinessInfoDetailView(LoginRequiredMixin, DetailView):
    """Display business information"""
    model = BusinessInfo
    template_name = 'core/business_info.html'
    context_object_name = 'business'

    def get_object(self):
        # Return the active business info or None
        return BusinessInfo.objects.filter(is_active=True).first()


class BusinessInfoUpdateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    """Update business information (Admin/IT Admin only)"""
    model = BusinessInfo
    form_class = BusinessInfoForm
    template_name = 'core/business_info_form.html'
    success_url = reverse_lazy('core:business_info')
    success_message = "Business information has been updated successfully!"

    def test_func(self):
        return self.request.user.role == User.IS_IT_ADMIN or self.request.user.is_staff

    def get_object(self):
        # Get or create active business info
        obj, created = BusinessInfo.objects.get_or_create(
            is_active=True,
            defaults={'name': 'Your Company Name'}
        )
        return obj


class SocialMediaListView(LoginRequiredMixin, ListView):
    """List all social media links"""
    model = SocialMediaLink
    template_name = 'core/social_media_list.html'
    context_object_name = 'social_links'

    def get_queryset(self):
        return SocialMediaLink.objects.select_related('business').filter(
            business__is_active=True
        )


class SocialMediaCreateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, CreateView):
    """Create new social media link"""
    model = SocialMediaLink
    form_class = SocialMediaLinkForm
    template_name = 'core/social_media_form.html'
    success_url = reverse_lazy('core:social_media_list')
    success_message = "Social media link has been added successfully!"

    def test_func(self):
        return self.request.user.role == User.IS_IT_ADMIN or self.request.user.is_staff

    def form_valid(self, form):
        # Associate with active business
        business = BusinessInfo.objects.filter(is_active=True).first()
        if business:
            form.instance.business = business
        return super().form_valid(form)


class SocialMediaUpdateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    """Update social media link"""
    model = SocialMediaLink
    form_class = SocialMediaLinkForm
    template_name = 'core/social_media_form.html'
    success_url = reverse_lazy('core:social_media_list')
    success_message = "Social media link has been updated successfully!"

    def test_func(self):
        return self.request.user.role == User.IS_IT_ADMIN or self.request.user.is_staff


class SocialMediaDeleteView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView):
    """Delete social media link"""
    model = SocialMediaLink
    template_name = 'core/social_media_confirm_delete.html'
    success_url = reverse_lazy('core:social_media_list')
    success_message = "Social media link has been deleted successfully!"

    def test_func(self):
        return self.request.user.role == User.IS_IT_ADMIN or self.request.user.is_staff


class GlobalSearchView(LoginRequiredMixin, View):
    """Global search API for quick search functionality"""

    def get(self, request):
        query = request.GET.get('q', '').strip()
        if len(query) < 2:
            return JsonResponse({'results': []})

        results = []
        user = request.user

        user_role = getattr(user, 'role', None)

        search_query = query
        if query.startswith('EQ:'):
            search_query = query[3:].strip()

        equipment = Equipment.objects.filter(
            models.Q(serial_number__icontains=search_query) |
            models.Q(model_number__icontains=search_query) |
            models.Q(brand__name__icontains=search_query) |
            models.Q(tracking_id__icontains=search_query)
        ).select_related('brand', 'category')[:5]

        if not equipment:
            try:
                # Attempt to parse query as UUID only if initial text search yields no results
                from uuid import UUID
                uuid_obj = UUID(query)
                equipment = Equipment.objects.filter(id=uuid_obj).select_related('brand', 'category')[:5]
            except ValueError:
                pass

        for eq in equipment:
            results.append({
                'id': str(eq.id),
                'type': 'Equipment',
                'title': f"{eq.brand.name} {eq.model_number}",
                'subtitle': f"SN: {eq.serial_number}",
                'url': f"/inventory/equipment/{eq.id}/",
                'icon': 'package',
                'icon_color': 'text-blue-600',
                'icon_bg': 'bg-blue-100',
            })

        if user.is_staff or getattr(user, 'can_approve', False):
            from requests.models import Assignment
            assignments = Assignment.objects.filter(
                models.Q(equipment__serial_number__icontains=query) |
                models.Q(equipment__model_number__icontains=query) |
                models.Q(user__username__icontains=query)
            ).select_related('equipment', 'equipment__brand', 'user')[:5]
            for assign in assignments:
                results.append({
                    'id': str(assign.id),
                    'type': 'Assignment',
                    'title': f"{assign.equipment.brand.name} {assign.equipment.model_number}",
                    'subtitle': f"Assigned to {assign.user.username}",
                    'url': f"/inventory/equipment/{assign.equipment.id}/",
                    'icon': 'user-check',
                    'icon_color': 'text-teal-600',
                    'icon_bg': 'bg-teal-100',
                })

        # Search Requests (role-based visibility)
        requests_qs = Request.objects.all()
        if not user.is_staff and user_role != User.IS_IT_ADMIN:
            if getattr(user, 'can_approve', False):
                requests_qs = requests_qs.filter(models.Q(user=user) | models.Q(user__manager=user))
            else:
                requests_qs = requests_qs.filter(user=user)

        requests_filtered = requests_qs.filter(
            models.Q(reason__icontains=query) |
            models.Q(id__icontains=query)
        )[:5]

        for req in requests_filtered:
            results.append({
                'id': str(req.id),
                'type': 'Request',
                'title': f"{req.get_request_type_display()} - {req.get_status_display()}",
                'subtitle': f"By {req.user.username}",
                'url': f"/requests/{req.id}/",
                'icon': 'clipboard-list',
                'icon_color': 'text-purple-600',
                'icon_bg': 'bg-purple-100',
            })

        # Search Vendors (IT_ADMIN only)
        if user_role == User.IS_IT_ADMIN or user.is_staff:
            vendors = Vendor.objects.filter(
                models.Q(name__icontains=query) |
                models.Q(contact_person__icontains=query)
            )[:5]

            for vendor in vendors:
                results.append({
                    'id': str(vendor.id),
                    'type': 'Vendor',
                    'title': vendor.name,
                    'subtitle': vendor.contact_person or '',
                    'url': f"/inventory/vendors/{vendor.id}/",
                    'icon': 'building',
                    'icon_color': 'text-green-600',
                    'icon_bg': 'bg-green-100',
                })

            # Search Brands
            brands = Brand.objects.filter(
                models.Q(name__icontains=query)
            )[:5]
            for brand in brands:
                results.append({
                    'id': str(brand.id),
                    'type': 'Brand',
                    'title': brand.name,
                    'subtitle': brand.website or 'No website',
                    'url': f"/inventory/brands/{brand.id}/",
                    'icon': 'award',
                    'icon_color': 'text-amber-600',
                    'icon_bg': 'bg-amber-100',
                })

            # Search Categories
            categories = Category.objects.filter(
                models.Q(name__icontains=query) |
                models.Q(description__icontains=query)
            )[:5]
            for cat in categories:
                results.append({
                    'id': str(cat.id),
                    'type': 'Category',
                    'title': cat.name,
                    'subtitle': cat.description[:50] if cat.description else 'No description',
                    'url': f"/inventory/categories/{cat.id}/",
                    'icon': 'folder',
                    'icon_color': 'text-indigo-600',
                    'icon_bg': 'bg-indigo-100',
                })

        # Search Users (for IT_ADMIN and Managers)
        if user.is_staff or user_role == User.IS_IT_ADMIN or getattr(user, 'can_approve', False):
            users = User.objects.filter(
                models.Q(username__icontains=query) |
                models.Q(first_name__icontains=query) |
                models.Q(last_name__icontains=query) |
                models.Q(email__icontains=query)
            )[:5]
            for u in users:
                results.append({
                    'id': str(u.id),
                    'type': 'User' if u.role != User.IS_IT_ADMIN else 'Staff',
                    'title': f"{u.get_full_name() or u.username}",
                    'subtitle': f"{u.email} ({u.get_role_display()})",
                    'url': "/accounts/profile/",
                    'icon': 'users' if u.role != User.IS_IT_ADMIN else 'shield',
                    'icon_color': 'text-cyan-600',
                    'icon_bg': 'bg-cyan-100',
                })

        # Search Notifications (if user has access)
        if hasattr(user, 'notifications'):
            from notifications.models import Notification
            notifications = Notification.objects.filter(
                recipient=user
            ).filter(
                models.Q(title__icontains=query) |
                models.Q(message__icontains=query)
            )[:5]
            for notif in notifications:
                results.append({
                    'id': str(notif.id),
                    'type': 'Notification',
                    'title': notif.title[:40],
                    'subtitle': notif.message[:50] if notif.message else '',
                    'url': f"/notifications/",
                    'icon': 'bell',
                    'icon_color': 'text-red-600',
                    'icon_bg': 'bg-red-100',
                })

        return JsonResponse({'results': results})
