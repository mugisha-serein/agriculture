"""Management status choices for audited request actions."""

from django.db.models import TextChoices


class AuditManagementStatus(TextChoices):
    """Workflow states for managed audit request actions."""

    NEW = 'new', 'New'
    IN_REVIEW = 'in_review', 'In Review'
    RESOLVED = 'resolved', 'Resolved'
    ESCALATED = 'escalated', 'Escalated'
