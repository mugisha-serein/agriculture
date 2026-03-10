"""Serializers for verification API endpoints."""

from rest_framework import serializers

from verification.domain.statuses import VerificationDocumentType
from verification.domain.statuses import VerificationStatus
from verification.models import UserVerification


class VerificationSubmissionSerializer(serializers.Serializer):
    """Input serializer for KYC document submission."""

    document_type = serializers.ChoiceField(choices=VerificationDocumentType.choices)
    document_number = serializers.CharField(max_length=64)
    document_front = serializers.FileField()
    document_back = serializers.FileField(required=False, allow_null=True)
    selfie = serializers.FileField(required=False, allow_null=True)
    activation_token = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class VerificationSummarySerializer(serializers.ModelSerializer):
    """Output serializer for verification records."""

    user_id = serializers.IntegerField(source='user.id', read_only=True)
    reviewer_id = serializers.IntegerField(source='reviewed_by.id', read_only=True, allow_null=True)

    class Meta:
        model = UserVerification
        fields = (
            'id',
            'user_id',
            'status',
            'document_type',
            'document_number',
            'document_front',
            'document_back',
            'selfie',
            'submitted_at',
            'reviewed_at',
            'reviewer_id',
            'admin_notes',
            'rejection_reason',
            'is_current',
        )


class VerificationReviewSerializer(serializers.Serializer):
    """Input serializer for admin verification decision."""

    decision = serializers.ChoiceField(
        choices=[VerificationStatus.APPROVED, VerificationStatus.REJECTED]
    )
    admin_notes = serializers.CharField(required=False, allow_blank=True)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
