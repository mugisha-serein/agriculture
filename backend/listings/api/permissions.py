"""Permission classes for marketplace API endpoints."""

from rest_framework.permissions import BasePermission


class IsSellerOrAdmin(BasePermission):
    """Allow access only to seller or admin users."""

    def has_permission(self, request, view):
        """Return whether request user can perform seller operations."""
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_staff or getattr(user, 'role', None) == 'admin':
            return True
        return getattr(user, 'role', None) == 'seller'
