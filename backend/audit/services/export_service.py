"""Pipeline service for exporting audit material to regulated audiences."""

from django.utils import timezone

from audit.api.serializers import AuditEventSerializer
from audit.models import AuditEvent


class AuditExportService:
    """Export audit rows with export metadata for compliance teams."""

    DEFAULT_LIMIT = 1000
    MAX_LIMIT = 5000

    def export(self, *, audience, since=None, limit=None):
        """Return serialized audit events for the requested audience."""
        effective_limit = min(
            int(limit or self.DEFAULT_LIMIT),
            self.MAX_LIMIT,
        )
        queryset = AuditEvent.objects.order_by('-occurred_at')
        if since is not None:
            queryset = queryset.filter(occurred_at__gte=since)
        rows = list(queryset[:effective_limit])
        serialized = AuditEventSerializer(rows, many=True).data
        return {
            'pipeline': 'audit_exports',
            'audience': audience,
            'exported_at': timezone.now().isoformat(),
            'event_count': len(serialized),
            'limit': effective_limit,
            'events': serialized,
        }
