"""Verification service workflows for KYC submission and admin review."""

import hashlib

from django.db import transaction
from django.utils import timezone
from django_q.tasks import async_task
from rest_framework.exceptions import PermissionDenied, ValidationError

from verification.domain.statuses import VerificationStatus
from verification.models import (
    UserVerification,
    VerificationDocument,
    VerificationReview,
    VerificationFraudCheck,
    VerificationStatusLog,
    VerificationSelfie,
)


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
        expiry_date=None,
    ):
        """Submit a new verification request and retire prior current records."""
        UserVerification.objects.filter(user=user, is_current=True).update(is_current=False)
        verification = UserVerification.objects.create(
            user=user,
            status=VerificationStatus.PENDING,
            submitted_at=timezone.now(),
            status_changed_at=timezone.now(),
            is_current=True,
        )
        VerificationStatusLog.objects.create(
            verification=verification,
            previous_status=VerificationStatus.PENDING,
            new_status=VerificationStatus.PENDING,
            changed_at=verification.submitted_at,
            change_reason='submitted',
            change_metadata={},
        )
        document = VerificationDocument.objects.create(
            verification=verification,
            document_type=document_type,
            document_number_hash=self._hash_document_number(document_number),
            document_number_last4=self._document_number_last4(document_number),
            document_front=document_front,
            document_back=document_back,
            expiry_date=expiry_date,
            document_metadata=self._build_document_metadata(
                document_front=document_front,
                document_back=document_back,
                expiry_date=expiry_date,
            ),
        )
        self._run_fraud_checks(verification=verification, documents=[document])
        if selfie:
            VerificationSelfie.objects.create(
                verification=verification,
                image=selfie,
                comparison_metadata={
                    'submitted': True,
                },
            )
        self._schedule_automated_checks(verification_id=verification.id)
        return verification

    def get_current_verification(self, *, user):
        """Return the current verification record for a user if available."""
        return (
            UserVerification.objects.select_related('reviewed_by')
            .prefetch_related(
                'documents__document_type',
                'selfies',
                'reviews',
                'status_logs',
                'fraud_checks',
            )
            .filter(user=user, is_current=True)
            .first()
        )

    def list_pending(self):
        """Return all pending verification records for admin review."""
        return UserVerification.objects.select_related('user').prefetch_related(
            'documents__document_type',
            'selfies',
            'reviews',
            'status_logs',
            'fraud_checks',
        ).filter(
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
        review_notes='',
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

        previous_status = verification.status
        verification.status = decision
        verification.reviewed_by = reviewer
        verification.reviewed_at = timezone.now()
        verification.review_notes = review_notes
        verification.rejection_reason = rejection_reason
        verification.status_changed_at = timezone.now()
        verification.save(
            update_fields=[
                'status',
                'reviewed_by',
                'reviewed_at',
                'review_notes',
                'rejection_reason',
                'status_changed_at',
                'updated_at',
            ]
        )
        VerificationReview.objects.create(
            verification=verification,
            reviewer=reviewer,
            previous_status=previous_status,
            new_status=decision,
            review_notes=review_notes,
            rejection_reason=rejection_reason,
            reviewed_at=verification.reviewed_at,
            review_metadata={},
        )
        VerificationStatusLog.objects.create(
            verification=verification,
            previous_status=previous_status,
            new_status=decision,
            changed_at=verification.status_changed_at,
            change_reason='reviewed',
            change_metadata={},
        )
        # Update User.is_verified if approved
        if decision == VerificationStatus.APPROVED:
            verification.user.is_verified = True
            verification.user.save(update_fields=['is_verified', 'updated_at'])

        return verification

    @staticmethod
    def _hash_document_number(document_number):
        """Return a deterministic hash for document number storage."""
        normalized = VerificationService._normalize_document_number(document_number)
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    @staticmethod
    def _document_number_last4(document_number):
        """Return the last four characters of the normalized document number."""
        normalized = VerificationService._normalize_document_number(document_number)
        return normalized[-4:] if len(normalized) >= 4 else normalized

    @staticmethod
    def _normalize_document_number(document_number):
        """Normalize document numbers for consistent hashing."""
        return ''.join((document_number or '').strip().upper().split())

    @staticmethod
    def _build_document_metadata(*, document_front, document_back=None, expiry_date=None):
        """Return metadata for uploaded verification documents."""
        return {
            'front': VerificationService._file_metadata(document_front),
            'back': VerificationService._file_metadata(document_back),
            'expiry_date': expiry_date.isoformat() if expiry_date else None,
        }

    @staticmethod
    def _file_metadata(upload):
        """Return minimal metadata for an uploaded file."""
        if upload is None:
            return {}
        return {
            'name': getattr(upload, 'name', ''),
            'size': getattr(upload, 'size', None),
            'content_type': getattr(upload, 'content_type', ''),
        }

    @staticmethod
    def _schedule_automated_checks(*, verification_id):
        """Queue stub automated checks for verification processing."""
        async_task('verification.tasks.run_ocr_pipeline', verification_id)
        async_task('verification.tasks.run_face_match', verification_id)
        async_task('verification.tasks.run_document_fraud_detection', verification_id)

    def _run_fraud_checks(self, *, verification, documents=None):
        """Run fraud checks for a verification submission."""
        signals = {}
        duplicate_count, duplicate_users = self._duplicate_document_usage(
            verification, documents=documents
        )
        if duplicate_count:
            signals['duplicate_document_hash'] = {
                'count': duplicate_count,
                'user_ids': duplicate_users,
            }
        risk_score = 0.0
        risk_level = 'low'
        is_flagged = False
        if duplicate_count:
            risk_score = 75.0
            risk_level = 'high'
            is_flagged = True
        VerificationFraudCheck.objects.create(
            verification=verification,
            risk_score=risk_score,
            risk_level=risk_level,
            verdict='flagged' if is_flagged else 'clear',
            signals=signals,
            is_flagged=is_flagged,
        )

    @staticmethod
    def _duplicate_document_usage(verification, documents=None):
        """Return duplicate document usage stats across users."""
        if documents is None:
            document_hashes = list(
                verification.documents.values_list('document_number_hash', flat=True)
            )
        else:
            document_hashes = [doc.document_number_hash for doc in documents]
        if not document_hashes:
            return 0, []
        duplicates = (
            VerificationDocument.objects.filter(document_number_hash__in=document_hashes)
            .exclude(verification_id=verification.id)
            .values_list('verification__user_id', flat=True)
            .distinct()
        )
        duplicate_users = list(duplicates)
        return len(duplicate_users), duplicate_users
