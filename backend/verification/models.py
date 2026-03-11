"""Verification domain models for KYC workflows."""

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from verification.domain.statuses import VerificationStatus


class TimestampedModel(models.Model):
    """Abstract model with creation and update timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserVerification(TimestampedModel):
    """KYC submission and review record for a user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='verifications',
    )
    status = models.CharField(
        max_length=16,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    submitted_at = models.DateTimeField(default=timezone.now)
    status_changed_at = models.DateTimeField(default=timezone.now)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='reviewed_verifications',
        blank=True,
        null=True,
    )
    review_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    is_current = models.BooleanField(default=True)

    class Meta:
        db_table = 'user_verifications'
        ordering = ['-submitted_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=Q(is_current=True),
                name='unique_current_verification_per_user',
            )
        ]

    def __str__(self):
        """Return a readable representation of a verification record."""
        return f'{self.user_id}:{self.status}:{self.id}'


class VerificationDocument(TimestampedModel):
    """Document files submitted for a verification request."""

    verification = models.ForeignKey(
        UserVerification,
        on_delete=models.CASCADE,
        related_name='documents',
    )
    document_type = models.ForeignKey(
        'VerificationDocumentType',
        on_delete=models.PROTECT,
        related_name='documents',
    )
    document_number_hash = models.CharField(max_length=64)
    document_number_last4 = models.CharField(max_length=4, blank=True)
    document_front = models.FileField(upload_to='verification/front/')
    document_back = models.FileField(upload_to='verification/back/', blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    document_metadata = models.JSONField(default=dict)

    class Meta:
        db_table = 'verification_documents'
        ordering = ['-created_at']

    def __str__(self):
        """Return a readable representation of the verification document."""
        return f'{self.verification_id}:{self.document_type_id}:{self.id}'


class VerificationSelfie(TimestampedModel):
    """Selfie images submitted for biometric verification."""

    verification = models.ForeignKey(
        UserVerification,
        on_delete=models.CASCADE,
        related_name='selfies',
    )
    document = models.ForeignKey(
        VerificationDocument,
        on_delete=models.SET_NULL,
        related_name='selfies',
        null=True,
        blank=True,
    )
    image = models.FileField(upload_to='verification/selfie/')
    face_match_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    face_match_status = models.CharField(max_length=32, blank=True)
    comparison_provider = models.CharField(max_length=64, blank=True)
    comparison_metadata = models.JSONField(default=dict)
    compared_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'verification_selfies'
        ordering = ['-created_at']

    def __str__(self):
        """Return a readable representation of the verification selfie."""
        return f'{self.verification_id}:{self.id}'


class VerificationReview(TimestampedModel):
    """Review decision and audit record for a verification."""

    verification = models.ForeignKey(
        UserVerification,
        on_delete=models.CASCADE,
        related_name='reviews',
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='verification_reviews',
        null=True,
        blank=True,
    )
    previous_status = models.CharField(max_length=16, choices=VerificationStatus.choices)
    new_status = models.CharField(max_length=16, choices=VerificationStatus.choices)
    review_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(default=timezone.now)
    review_metadata = models.JSONField(default=dict)

    class Meta:
        db_table = 'verification_reviews'
        ordering = ['-reviewed_at']

    def __str__(self):
        """Return a readable representation of the verification review."""
        return f'{self.verification_id}:{self.new_status}:{self.id}'


class VerificationStatusLog(TimestampedModel):
    """Historical status changes for verification lifecycle auditing."""

    verification = models.ForeignKey(
        UserVerification,
        on_delete=models.CASCADE,
        related_name='status_logs',
    )
    previous_status = models.CharField(max_length=16, choices=VerificationStatus.choices)
    new_status = models.CharField(max_length=16, choices=VerificationStatus.choices)
    changed_at = models.DateTimeField(default=timezone.now)
    change_reason = models.CharField(max_length=255, blank=True)
    change_metadata = models.JSONField(default=dict)

    class Meta:
        db_table = 'verification_status_logs'
        ordering = ['-changed_at']

    def __str__(self):
        """Return a readable representation of the status log."""
        return f'{self.verification_id}:{self.previous_status}->{self.new_status}'


class VerificationFraudCheck(TimestampedModel):
    """Fraud detection signals and risk scoring for verifications."""

    verification = models.ForeignKey(
        UserVerification,
        on_delete=models.CASCADE,
        related_name='fraud_checks',
    )
    risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    risk_level = models.CharField(max_length=16, blank=True)
    verdict = models.CharField(max_length=32, blank=True)
    signals = models.JSONField(default=dict)
    is_flagged = models.BooleanField(default=False)
    checked_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'verification_fraud_checks'
        ordering = ['-checked_at']

    def __str__(self):
        """Return a readable representation of the fraud check."""
        return f'{self.verification_id}:{self.risk_level}:{self.id}'


class VerificationDocumentType(TimestampedModel):
    """Managed document types accepted for verification."""

    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=120)
    requires_back_image = models.BooleanField(default=False)
    requires_expiry_date = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'verification_document_types'
        ordering = ['name']

    def __str__(self):
        """Return a readable representation of a document type."""
        return f'{self.code}:{self.name}'
