"""Alert taxonomy for real-time audit notifications."""

from django.db.models import TextChoices


class AlertSeverity(TextChoices):
    """Severity levels for audit alerts."""

    WARNING = 'warning', 'Warning'
    CRITICAL = 'critical', 'Critical'


class AlertType(TextChoices):
    """Domain-specific alert triggers."""

    ADMIN_PRIVILEGE_CHANGE = 'admin_privilege_change', 'Admin Privilege Change'
    LARGE_REFUND = 'large_refund', 'Large Refund'
    ACCOUNT_SUSPENSION = 'account_suspension', 'Account Suspension'
