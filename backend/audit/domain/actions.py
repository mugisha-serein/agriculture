"""Audit action choices."""

from django.db.models import TextChoices


class AuditAction(TextChoices):
    """Supported audit event action types."""

    CREATE = 'create', 'Create'
    UPDATE = 'update', 'Update'
    DELETE = 'delete', 'Delete'
    CUSTOM = 'custom', 'Custom'
