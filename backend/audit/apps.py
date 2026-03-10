"""App configuration for auditability domain."""

from django.apps import AppConfig


class AuditConfig(AppConfig):
    """Configuration for system-wide auditability."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audit'
    verbose_name = 'Audit'

    def ready(self):
        """Load signal registrations for model change auditing."""
        import audit.signals
