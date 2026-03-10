"""Permission classes for payments endpoints."""

from rest_framework.permissions import BasePermission


class IsPaymentAdmin(BasePermission):
    """Allow access only to payment administrators."""

    def has_permission(self, request, view):
        """Return whether current user can access admin payment operations."""
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.is_staff or getattr(user, 'role', None) == 'admin'
