"""Permission classes for audit APIs."""

from rest_framework.permissions import BasePermission


class IsAuditAdmin(BasePermission):
    """Allow access to audit APIs for admin users only."""

    def has_permission(self, request, view):
        """Return whether current user can access audit endpoints."""
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.is_staff or getattr(user, 'role', None) == 'admin'
