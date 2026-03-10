"""Admin registrations for reputation models."""

from django.contrib import admin

from reputation.models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Admin configuration for reputation reviews."""

    list_display = ('id', 'order', 'reviewer', 'reviewee', 'rating', 'is_visible', 'created_at')
    list_filter = ('rating', 'is_visible')
    search_fields = ('order__order_number', 'reviewer__email', 'reviewee__email', 'comment')
    ordering = ('-created_at',)
