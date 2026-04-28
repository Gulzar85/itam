from django.contrib.auth.mixins import UserPassesTestMixin


class ITAdminRequiredMixin(UserPassesTestMixin):
    """Mixin to require IT Admin role for access to views"""

    def test_func(self):
        return hasattr(self.request.user, 'role') and self.request.user.role == 'IT_ADMIN'


class ManagerOrAdminRequiredMixin(UserPassesTestMixin):
    """Mixin to require Manager or IT Admin role for access to views"""

    def test_func(self):
        user = self.request.user
        return hasattr(user, 'role') and (user.role == 'IT_ADMIN' or getattr(user, 'can_approve', False))
