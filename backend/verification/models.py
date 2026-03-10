"""Verification domain models for KYC workflows."""

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from verification.domain.statuses import VerificationDocumentType
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
    document_type = models.CharField(
        max_length=32,
        choices=VerificationDocumentType.choices,
    )
    document_number = models.CharField(max_length=64)
    document_front = models.FileField(upload_to='verification/front/')
    document_back = models.FileField(upload_to='verification/back/', blank=True, null=True)
    selfie = models.FileField(upload_to='verification/selfie/', blank=True, null=True)
    submitted_at = models.DateTimeField(default=timezone.now)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='reviewed_verifications',
        blank=True,
        null=True,
    )
    admin_notes = models.TextField(blank=True)
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
