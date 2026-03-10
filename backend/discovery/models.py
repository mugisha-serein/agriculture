"""Discovery persistence models for search telemetry."""

from django.conf import settings
from django.db import models
from django.utils import timezone

from discovery.domain.sorting import DiscoverySort


class TimestampedModel(models.Model):
    """Abstract base model with audit timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SearchQueryLog(TimestampedModel):
    """Search metadata log without storing marketplace product copies."""

    searched_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='discovery_search_logs',
    )
    query_text = models.CharField(max_length=255, blank=True)
    filters = models.JSONField(default=dict)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    radius_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sort_by = models.CharField(
        max_length=16,
        choices=DiscoverySort.choices,
        default=DiscoverySort.RELEVANCE,
    )
    page = models.PositiveIntegerField(default=1)
    page_size = models.PositiveIntegerField(default=20)
    result_count = models.PositiveIntegerField(default=0)
    searched_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'search_queries'
        ordering = ['-searched_at']

    def __str__(self):
        """Return readable representation for admin and debugging."""
        return f'{self.query_text}:{self.result_count}:{self.id}'
