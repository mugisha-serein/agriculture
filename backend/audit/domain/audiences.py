"""Audience definitions for audit export pipelines."""

from django.db.models import TextChoices


class AuditAudience(TextChoices):
    """Supported recipients for audit export pipelines."""

    REGULATORS = 'regulators', 'Regulators'
    COMPLIANCE = 'compliance', 'Compliance'
    LEGAL = 'legal', 'Legal'
