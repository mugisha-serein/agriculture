"""Serializers for verification API endpoints."""

from rest_framework import serializers

from verification.domain.statuses import VerificationStatus
from verification.models import (
    UserVerification,
    VerificationDocument,
    VerificationDocumentType,
    VerificationSelfie,
)


class VerificationSubmissionSerializer(serializers.Serializer):
    """Input serializer for KYC document submission."""

    document_type = serializers.SlugRelatedField(
        slug_field='code',
        queryset=VerificationDocumentType.objects.filter(is_active=True),
    )
    document_number = serializers.CharField(max_length=64)
    document_front = serializers.FileField()
    document_back = serializers.FileField(required=False, allow_null=True)
    selfie = serializers.FileField(required=False, allow_null=True)
    expiry_date = serializers.DateField(required=False, allow_null=True)
    activation_token = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def validate(self, attrs):
        """Validate document requirements based on type."""
        document_type = attrs.get('document_type')
        document_back = attrs.get('document_back')
        expiry_date = attrs.get('expiry_date')
        if document_type:
            if document_type.requires_back_image and not document_back:
                raise serializers.ValidationError(
                    {'document_back': 'Back image is required for this document type.'}
                )
            if document_type.requires_expiry_date and not expiry_date:
                raise serializers.ValidationError(
                    {'expiry_date': 'Expiry date is required for this document type.'}
                )
        return attrs


class VerificationSummarySerializer(serializers.ModelSerializer):
    """Output serializer for verification records."""

    user_id = serializers.IntegerField(source='user.id', read_only=True)
    reviewer_id = serializers.IntegerField(source='reviewed_by.id', read_only=True, allow_null=True)
    admin_notes = serializers.CharField(source='review_notes', read_only=True)
    documents = serializers.SerializerMethodField()
    selfies = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()
    status_logs = serializers.SerializerMethodField()
    fraud_checks = serializers.SerializerMethodField()

    def get_documents(self, obj):
        """Return documents submitted for the verification."""
        documents = getattr(obj, 'documents', None)
        if documents is None:
            documents = obj.documents.all()
        return VerificationDocumentSerializer(documents, many=True).data

    def get_selfies(self, obj):
        """Return selfies submitted for the verification."""
        selfies = getattr(obj, 'selfies', None)
        if selfies is None:
            selfies = obj.selfies.all()
        return VerificationSelfieSerializer(selfies, many=True).data

    def get_reviews(self, obj):
        """Return review history for the verification."""
        reviews = getattr(obj, 'reviews', None)
        if reviews is None:
            reviews = obj.reviews.all()
        return VerificationReviewSerializer(reviews, many=True).data

    def get_status_logs(self, obj):
        """Return status change history for the verification."""
        logs = getattr(obj, 'status_logs', None)
        if logs is None:
            logs = obj.status_logs.all()
        return VerificationStatusLogSerializer(logs, many=True).data

    def get_fraud_checks(self, obj):
        """Return fraud checks for the verification."""
        checks = getattr(obj, 'fraud_checks', None)
        if checks is None:
            checks = obj.fraud_checks.all()
        return VerificationFraudCheckSerializer(checks, many=True).data

    class Meta:
        model = UserVerification
        fields = (
            'id',
            'user_id',
            'status',
            'submitted_at',
            'status_changed_at',
            'reviewed_at',
            'reviewer_id',
            'admin_notes',
            'rejection_reason',
            'is_current',
            'documents',
            'selfies',
            'reviews',
            'status_logs',
            'fraud_checks',
        )


class VerificationReviewInputSerializer(serializers.Serializer):
    """Input serializer for admin verification decisions."""

    status = serializers.ChoiceField(
        choices=[VerificationStatus.APPROVED, VerificationStatus.REJECTED],
        required=False,
    )
    decision = serializers.ChoiceField(
        choices=[VerificationStatus.APPROVED, VerificationStatus.REJECTED],
        required=False,
        write_only=True,
    )
    review_notes = serializers.CharField(required=False, allow_blank=True)
    admin_notes = serializers.CharField(required=False, allow_blank=True, write_only=True)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        """Normalize legacy fields and enforce rejection requirements."""
        status_value = attrs.get('status') or attrs.get('decision')
        if not status_value:
            raise serializers.ValidationError({'status': 'This field is required.'})
        attrs['status'] = status_value

        if not attrs.get('review_notes') and attrs.get('admin_notes'):
            attrs['review_notes'] = attrs['admin_notes']

        if status_value == VerificationStatus.REJECTED and not attrs.get(
            'rejection_reason', ''
        ).strip():
            raise serializers.ValidationError(
                {'rejection_reason': 'Rejection reason is required.'}
            )
        return attrs


class VerificationDocumentSerializer(serializers.ModelSerializer):
    """Output serializer for verification documents."""

    document_type = serializers.SlugRelatedField(slug_field='code', read_only=True)

    class Meta:
        model = VerificationDocument
        fields = (
            'id',
            'document_type',
            'document_number_last4',
            'document_front',
            'document_back',
            'expiry_date',
            'document_metadata',
            'created_at',
        )


class VerificationSelfieSerializer(serializers.ModelSerializer):
    """Output serializer for verification selfies."""

    class Meta:
        model = VerificationSelfie
        fields = (
            'id',
            'image',
            'face_match_score',
            'face_match_status',
            'comparison_provider',
            'comparison_metadata',
            'compared_at',
            'created_at',
        )


class VerificationReviewSerializer(serializers.Serializer):
    """Output serializer for verification reviews."""

    id = serializers.IntegerField(read_only=True)
    reviewer_id = serializers.IntegerField(source='reviewer.id', read_only=True, allow_null=True)
    previous_status = serializers.CharField()
    new_status = serializers.CharField()
    review_notes = serializers.CharField(allow_blank=True)
    rejection_reason = serializers.CharField(allow_blank=True)
    reviewed_at = serializers.DateTimeField()


class VerificationStatusLogSerializer(serializers.Serializer):
    """Output serializer for verification status logs."""

    id = serializers.IntegerField(read_only=True)
    previous_status = serializers.CharField()
    new_status = serializers.CharField()
    changed_at = serializers.DateTimeField()
    change_reason = serializers.CharField(allow_blank=True)
    change_metadata = serializers.JSONField()


class VerificationFraudCheckSerializer(serializers.Serializer):
    """Output serializer for verification fraud checks."""

    id = serializers.IntegerField(read_only=True)
    risk_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    risk_level = serializers.CharField()
    verdict = serializers.CharField()
    signals = serializers.JSONField()
    is_flagged = serializers.BooleanField()
    checked_at = serializers.DateTimeField()
