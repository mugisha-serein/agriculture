from django.contrib import admin
from discovery.models import SearchQueryLog, PlatformSystem


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


@admin.register(PlatformSystem)
class PlatformSystemAdmin(admin.ModelAdmin):
    """Admin configuration for platform systems."""

    list_display = ('id', 'name', 'icon', 'position', 'is_active')
    list_editable = ('position', 'is_active')
    search_fields = ('name', 'description')
    ordering = ('position', 'name')
