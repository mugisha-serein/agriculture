"""Admin registrations for verification models."""

from django.contrib import admin

from verification.models import (
    UserVerification,
    VerificationDocument,
    VerificationDocumentType,
    VerificationReview,
    VerificationFraudCheck,
    VerificationStatusLog,
    VerificationSelfie,
)


@admin.register(UserVerification)
class UserVerificationAdmin(admin.ModelAdmin):
    """Admin configuration for user verification records."""

    list_display = (
        'id',
        'user',
        'status',
        'document_count',
        'submitted_at',
        'reviewed_at',
        'is_current',
    )
    list_filter = ('status', 'is_current')
    search_fields = ('user__email', 'documents__document_number_last4')
    ordering = ('-submitted_at',)

    @staticmethod
    def document_count(obj):
        """Return the number of documents for the verification."""
        return obj.documents.count()


@admin.register(VerificationDocumentType)
class VerificationDocumentTypeAdmin(admin.ModelAdmin):
    """Admin configuration for document types."""

    list_display = (
        'id',
        'code',
        'name',
        'requires_back_image',
        'requires_expiry_date',
        'is_active',
        'created_at',
    )
    list_filter = ('is_active',)
    search_fields = ('code', 'name')
    ordering = ('name',)


@admin.register(VerificationDocument)
class VerificationDocumentAdmin(admin.ModelAdmin):
    """Admin configuration for verification documents."""

    list_display = (
        'id',
        'verification',
        'document_type',
        'document_number_last4',
        'expiry_date',
        'created_at',
    )
    list_filter = ('document_type',)
    search_fields = ('verification__user__email', 'document_number_last4')
    ordering = ('-created_at',)


@admin.register(VerificationSelfie)
class VerificationSelfieAdmin(admin.ModelAdmin):
    """Admin configuration for verification selfies."""

    list_display = (
        'id',
        'verification',
        'document',
        'face_match_score',
        'face_match_status',
        'comparison_provider',
        'created_at',
    )
    list_filter = ('face_match_status', 'comparison_provider')
    search_fields = ('verification__user__email',)
    ordering = ('-created_at',)


@admin.register(VerificationReview)
class VerificationReviewAdmin(admin.ModelAdmin):
    """Admin configuration for verification reviews."""

    list_display = (
        'id',
        'verification',
        'reviewer',
        'previous_status',
        'new_status',
        'reviewed_at',
    )
    list_filter = ('new_status',)
    search_fields = ('verification__user__email', 'reviewer__email')
    ordering = ('-reviewed_at',)


@admin.register(VerificationStatusLog)
class VerificationStatusLogAdmin(admin.ModelAdmin):
    """Admin configuration for verification status logs."""

    list_display = (
        'id',
        'verification',
        'previous_status',
        'new_status',
        'changed_at',
    )
    list_filter = ('new_status',)
    search_fields = ('verification__user__email',)
    ordering = ('-changed_at',)


@admin.register(VerificationFraudCheck)
class VerificationFraudCheckAdmin(admin.ModelAdmin):
    """Admin configuration for verification fraud checks."""

    list_display = (
        'id',
        'verification',
        'risk_score',
        'risk_level',
        'verdict',
        'is_flagged',
        'checked_at',
    )
    list_filter = ('risk_level', 'verdict', 'is_flagged')
    search_fields = ('verification__user__email',)
    ordering = ('-checked_at',)
