"""Verification status and document type definitions."""

from django.db.models import TextChoices


class VerificationStatus(TextChoices):
    """Lifecycle statuses for account verification records."""

    PENDING = 'pending', 'Pending'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'


class VerificationDocumentType(TextChoices):
    """Document types accepted during KYC submission."""

    NATIONAL_ID = 'national_id', 'National ID'
    PASSPORT = 'passport', 'Passport'
    DRIVER_LICENSE = 'driver_license', 'Driver License'
    BUSINESS_REGISTRATION = 'business_registration', 'Business Registration'
