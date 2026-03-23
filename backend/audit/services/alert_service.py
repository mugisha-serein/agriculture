"""Real-time alerting for high-suspicion audit events."""

from decimal import Decimal

from django.conf import settings
from django.utils import timezone

from audit.domain.alerts import AlertSeverity
from audit.domain.alerts import AlertType
from audit.models import AuditAlert


class AuditAlertService:
    """Evaluate audit event data and persist alerts for critical signals."""

    DEFAULT_LARGE_REFUND_THRESHOLD = Decimal('1000.00')

    def __init__(self):
        threshold_value = getattr(settings, 'AUDIT_LARGE_REFUND_THRESHOLD', self.DEFAULT_LARGE_REFUND_THRESHOLD)
        self.large_refund_threshold = Decimal(str(threshold_value))

    def notify(self, *, event):
        """Evaluate audit event and emit alerts for each matching rule."""
        alert_payloads = [
            self._detect_admin_privilege_change(event=event),
            self._detect_account_suspension(event=event),
            self._detect_large_refund(event=event),
        ]
        alerts = []
        for payload in filter(None, alert_payloads):
            alerts.append(self._create_alert(event=event, **payload))
        return alerts

    def _detect_admin_privilege_change(self, *, event):
        """Detect role updates that grant admin privileges."""
        if event.model_label != 'users.User':
            return None
        change_set = event.change_set or {}
        role_change = change_set.get('role')
        if role_change and role_change.get('to') == 'admin':
            return {
                'alert_type': AlertType.ADMIN_PRIVILEGE_CHANGE,
                'severity': AlertSeverity.CRITICAL,
                'description': 'Admin privileges granted to user.',
                'context': {'change': role_change},
            }
        is_staff_change = change_set.get('is_staff')
        if is_staff_change and is_staff_change.get('to') is True:
            return {
                'alert_type': AlertType.ADMIN_PRIVILEGE_CHANGE,
                'severity': AlertSeverity.CRITICAL,
                'description': 'Staff flag enabled via audit event.',
                'context': {'change': is_staff_change},
            }
        return None

    def _detect_account_suspension(self, *, event):
        """Detect when a user account is suspended."""
        if event.model_label != 'users.User':
            return None
        change_set = event.change_set or {}
        active_change = change_set.get('is_active')
        if active_change and active_change.get('from') and not active_change.get('to'):
            return {
                'alert_type': AlertType.ACCOUNT_SUSPENSION,
                'severity': AlertSeverity.WARNING,
                'description': 'Account suspended via audit trace.',
                'context': {'change': active_change},
            }
        return None

    def _detect_large_refund(self, *, event):
        """Detect refund transactions that exceed configured thresholds."""
        if event.model_label != 'payments.EscrowTransaction':
            return None
        change_set = event.change_set or {}
        transaction_type = change_set.get('transaction_type')
        if not transaction_type or transaction_type.get('to') != 'refund':
            return None
        amount_value = event.after_state.get('amount')
        if amount_value is None:
            return None
        amount = Decimal(str(amount_value))
        if amount < self.large_refund_threshold:
            return None
        return {
            'alert_type': AlertType.LARGE_REFUND,
            'severity': AlertSeverity.CRITICAL,
            'description': f'Large refund processed: {amount}.',
            'context': {
                'amount': str(amount),
                'currency': event.after_state.get('currency'),
                'change_set': transaction_type,
            },
        }

    def _create_alert(self, *, event, alert_type, severity, description, context):
        """Persist alert metadata linked to the audit event."""
        enriched_context = {
            'app_label': event.app_label,
            'model_label': event.model_label,
            'object_pk': event.object_pk,
            **(context or {}),
        }
        return AuditAlert.objects.create(
            event=event,
            alert_type=alert_type,
            severity=severity,
            description=description,
            context=enriched_context,
            triggered_by=event.actor,
            triggered_at=timezone.now(),
        )
