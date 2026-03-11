"""Async verification automation tasks (stub implementations)."""

from decimal import Decimal

from django.utils import timezone

from verification.models import VerificationDocument, VerificationFraudCheck, VerificationSelfie


def run_ocr_pipeline(verification_id):
    """Stub OCR pipeline for verification documents."""
    now = timezone.now()
    for document in VerificationDocument.objects.filter(verification_id=verification_id):
        metadata = dict(document.document_metadata or {})
        metadata['ocr'] = {
            'status': 'completed',
            'provider': 'stub',
            'text': '',
            'completed_at': now.isoformat(),
        }
        document.document_metadata = metadata
        document.save(update_fields=['document_metadata', 'updated_at'])


def run_face_match(verification_id):
    """Stub face match pipeline for verification selfies."""
    now = timezone.now()
    for selfie in VerificationSelfie.objects.filter(verification_id=verification_id):
        selfie.face_match_status = 'stub'
        selfie.face_match_score = Decimal('0.00')
        selfie.comparison_provider = 'stub'
        selfie.compared_at = now
        metadata = dict(selfie.comparison_metadata or {})
        metadata['face_match'] = {
            'status': 'completed',
            'provider': 'stub',
            'score': '0.00',
            'completed_at': now.isoformat(),
        }
        selfie.comparison_metadata = metadata
        selfie.save(
            update_fields=[
                'face_match_status',
                'face_match_score',
                'comparison_provider',
                'compared_at',
                'comparison_metadata',
                'updated_at',
            ]
        )


def run_document_fraud_detection(verification_id):
    """Stub document fraud detection for a verification submission."""
    now = timezone.now()
    documents = VerificationDocument.objects.filter(verification_id=verification_id)
    document_hashes = list(documents.values_list('document_number_hash', flat=True))
    duplicate_users = []
    if document_hashes:
        duplicate_users = list(
            VerificationDocument.objects.filter(document_number_hash__in=document_hashes)
            .exclude(verification_id=verification_id)
            .values_list('verification__user_id', flat=True)
            .distinct()
        )

    duplicate_count = len(duplicate_users)
    risk_score = Decimal('75.00') if duplicate_count else Decimal('0.00')
    risk_level = 'high' if duplicate_count else 'low'
    is_flagged = duplicate_count > 0

    signals = {
        'document_fraud_detection': {
            'status': 'completed',
            'provider': 'stub',
        },
        'duplicate_document_hash': {
            'count': duplicate_count,
            'user_ids': duplicate_users,
        },
    }

    fraud_check = (
        VerificationFraudCheck.objects.filter(verification_id=verification_id)
        .order_by('-checked_at')
        .first()
    )
    if fraud_check:
        fraud_check.risk_score = risk_score
        fraud_check.risk_level = risk_level
        fraud_check.verdict = 'flagged' if is_flagged else 'clear'
        fraud_check.signals = signals
        fraud_check.is_flagged = is_flagged
        fraud_check.checked_at = now
        fraud_check.save(
            update_fields=[
                'risk_score',
                'risk_level',
                'verdict',
                'signals',
                'is_flagged',
                'checked_at',
                'updated_at',
            ]
        )
    else:
        VerificationFraudCheck.objects.create(
            verification_id=verification_id,
            risk_score=risk_score,
            risk_level=risk_level,
            verdict='flagged' if is_flagged else 'clear',
            signals=signals,
            is_flagged=is_flagged,
            checked_at=now,
        )
