"""Verification status and document type definitions."""

from django.db.models import TextChoices


class VerificationStatus(TextChoices):
    """Lifecycle statuses for account verification records."""

    PENDING = 'pending', 'Pending'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'
