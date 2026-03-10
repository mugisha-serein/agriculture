"""Verification service workflows for KYC submission and admin review."""

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from verification.domain.statuses import VerificationStatus
from verification.models import UserVerification


class VerificationService:
    """Application service for verification workflows."""

    @transaction.atomic
    def submit_verification(
        self,
        *,
        user,
        document_type,
        document_number,
        document_front,
        document_back=None,
        selfie=None,
    ):
        """Submit a new verification request and retire prior current records."""
        UserVerification.objects.filter(user=user, is_current=True).update(is_current=False)
        return UserVerification.objects.create(
            user=user,
            status=VerificationStatus.PENDING,
            document_type=document_type,
            document_number=document_number,
            document_front=document_front,
            document_back=document_back,
            selfie=selfie,
            submitted_at=timezone.now(),
            is_current=True,
        )

    def get_current_verification(self, *, user):
        """Return the current verification record for a user if available."""
        return (
            UserVerification.objects.select_related('reviewed_by')
            .filter(user=user, is_current=True)
            .first()
        )

    def list_pending(self):
        """Return all pending verification records for admin review."""
        return UserVerification.objects.select_related('user').filter(
            status=VerificationStatus.PENDING,
            is_current=True,
        )

    @transaction.atomic
    def review_verification(
        self,
        *,
        reviewer,
        verification_id,
        decision,
        admin_notes='',
        rejection_reason='',
    ):
        """Review a pending verification and persist final decision fields."""
        if not (reviewer.is_staff or getattr(reviewer, 'role', None) == 'admin'):
            raise PermissionDenied('Only admins can review verifications.')

        try:
            verification = UserVerification.objects.select_related('user').get(
                id=verification_id,
                is_current=True,
            )
        except UserVerification.DoesNotExist as exc:
            raise ValidationError({'verification_id': ['Verification record was not found.']}) from exc

        if verification.status != VerificationStatus.PENDING:
            raise ValidationError({'verification_id': ['Verification is not pending review.']})
        if decision not in {VerificationStatus.APPROVED, VerificationStatus.REJECTED}:
            raise ValidationError({'decision': ['Decision must be approved or rejected.']})
        if decision == VerificationStatus.REJECTED and not rejection_reason.strip():
            raise ValidationError({'rejection_reason': ['Rejection reason is required.']})

        verification.status = decision
        verification.reviewed_by = reviewer
        verification.reviewed_at = timezone.now()
        verification.admin_notes = admin_notes
        verification.rejection_reason = rejection_reason
        verification.save(
            update_fields=[
                'status',
                'reviewed_by',
                'reviewed_at',
                'admin_notes',
                'rejection_reason',
                'updated_at',
            ]
        )
        # Update User.is_verified if approved
        if decision == VerificationStatus.APPROVED:
            verification.user.is_verified = True
            verification.user.save(update_fields=['is_verified', 'updated_at'])

        return verification
