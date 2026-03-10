"""Admin registrations for verification models."""

from django.contrib import admin

from verification.models import UserVerification


@admin.register(UserVerification)
class UserVerificationAdmin(admin.ModelAdmin):
    """Admin configuration for user verification records."""

    list_display = (
        'id',
        'user',
        'status',
        'document_type',
        'submitted_at',
        'reviewed_at',
        'is_current',
    )
    list_filter = ('status', 'document_type', 'is_current')
    search_fields = ('user__email', 'document_number')
    ordering = ('-submitted_at',)
