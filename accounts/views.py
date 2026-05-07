from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .forms import UserProfileForm, UserCreationForm
from django.views.generic import CreateView
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView
from django.contrib.auth.views import (
    PasswordChangeView, 
    PasswordResetView, 
    PasswordResetConfirmView
)
from django.views.generic.edit import UpdateView
from .forms import UserProfileForm, UserCreationForm

User = get_user_model()


class ProfileDetailView(LoginRequiredMixin, DetailView):
    """Optimized profile display[cite: 14]."""
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'profile_user'

    def get_object(self):
        # Ensure users can only view their own profile (prevent IDOR)
        # Force to current user regardless of URL parameter
        return User.objects.select_related('department', 'manager').get(
            pk=self.request.user.pk
        )


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Streamlined profile editing[cite: 14]."""
    model = User
    form_class = UserProfileForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Your profile has been updated successfully![cite: 14]')
        return super().form_valid(form)

class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """Secure password management with automated session updates[cite: 14]."""
    template_name = 'accounts/change_password.html'
    success_url = reverse_lazy('accounts:profile')

    def form_valid(self, form):
        messages.success(self.request, 'Your password has been changed successfully![cite: 14]')
        return super().form_valid(form)


from services.permissions import ITAdminRequiredMixin


class RegisterView(ITAdminRequiredMixin, CreateView):
    """
    User registration view for new employees.
    """
    model = User
    form_class = UserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Account created successfully for {form.cleaned_data["first_name"]} {form.cleaned_data["last_name"]}.'
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create Account'
        return context


class CustomPasswordResetView(PasswordResetView):
    """
    Custom password reset view.
    """
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.txt'
    success_url = reverse_lazy('accounts:password_reset_done')


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """
    Custom password reset confirm view.
    """
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')
