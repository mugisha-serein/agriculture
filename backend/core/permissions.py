"""Custom permissions for role-based access control and verification."""

from rest_framework import permissions

class IsVerifiedRole(permissions.BasePermission):
    """
    Permission check for verified sellers and transporters.
    Buyers are always allowed (as long as they are authenticated).
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        if not request.user or not request.user.is_authenticated:
            return False
        
        # Buyers don't need KYC verification for basic marketplace access
        if request.user.role == 'buyer':
            return True
        
        # Sellers and transporters must be verified by an admin
        return request.user.is_verified
