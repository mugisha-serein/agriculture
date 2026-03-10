"""Permission classes for verification endpoints."""

from rest_framework.permissions import BasePermission


class IsVerificationAdmin(BasePermission):
    """Allow access only to verification administrators."""

    def has_permission(self, request, view):
        """Return whether the current user can access admin verification endpoints."""
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.is_staff or getattr(user, 'role', None) == 'admin'
