"""Admin registrations for discovery models."""

from django.contrib import admin

from discovery.models import SearchQueryLog


@admin.register(SearchQueryLog)
class SearchQueryLogAdmin(admin.ModelAdmin):
    """Admin configuration for discovery search logs."""

    list_display = (
        'id',
        'query_text',
        'searched_by',
        'sort_by',
        'result_count',
        'searched_at',
    )
    list_filter = ('sort_by',)
    search_fields = ('query_text', 'searched_by__email')
    ordering = ('-searched_at',)
