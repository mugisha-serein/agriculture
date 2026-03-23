"""Audit models for immutable system-wide event tracking."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from audit.domain.actions import AuditAction
from audit.domain.alerts import AlertSeverity
from audit.domain.alerts import AlertType
from audit.domain.management import AuditManagementStatus


class AuditEvent(models.Model):
    """Immutable event record for audited domain mutations."""

    request_id = models.CharField(max_length=64, blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='audit_events',
        null=True,
        blank=True,
    )
    actor_email = models.EmailField(blank=True)
    source = models.CharField(max_length=32, default='model_signal')
    action = models.CharField(max_length=16, choices=AuditAction.choices)
    app_label = models.CharField(max_length=64)
    model_label = models.CharField(max_length=128)
    object_pk = models.CharField(max_length=64)
    object_repr = models.CharField(max_length=255, blank=True)
    request_path = models.CharField(max_length=255, blank=True)
    request_method = models.CharField(max_length=16, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    before_state = models.JSONField(default=dict)
    after_state = models.JSONField(default=dict)
    change_set = models.JSONField(default=dict)
    metadata = models.JSONField(default=dict)
    previous_hash = models.CharField(max_length=64, blank=True)
    event_hash = models.CharField(max_length=64, unique=True)
    occurred_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = 'audit_events'
        ordering = ['-id']

    def save(self, *args, **kwargs):
        """Persist immutable event on create only."""
        if self.pk is not None and AuditEvent.objects.filter(pk=self.pk).exists():
            raise ValidationError('Audit events are immutable.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Disallow event deletion to preserve audit trail integrity."""
        raise ValidationError('Audit events are immutable.')

    def __str__(self):
        """Return readable audit event identifier."""
        return f'{self.model_label}:{self.object_pk}:{self.action}:{self.id}'


class AuditRequestAction(models.Model):
    """Request-level audit action for monitored app endpoints."""

    request_id = models.CharField(max_length=64, blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='audit_request_actions',
        null=True,
        blank=True,
    )
    actor_email = models.EmailField(blank=True)
    app_scope = models.CharField(max_length=32)
    action_name = models.CharField(max_length=128)
    request_path = models.CharField(max_length=255)
    request_method = models.CharField(max_length=16)
    status_code = models.PositiveSmallIntegerField(default=0)
    succeeded = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    query_params = models.JSONField(default=dict)
    request_data = models.JSONField(default=dict)
    response_data = models.JSONField(default=dict)
    metadata = models.JSONField(default=dict)
    duration_ms = models.PositiveIntegerField(default=0)
    previous_hash = models.CharField(max_length=64, blank=True)
    event_hash = models.CharField(max_length=64, unique=True)
    management_status = models.CharField(
        max_length=16,
        choices=AuditManagementStatus.choices,
        default=AuditManagementStatus.NEW,
    )
    management_note = models.TextField(blank=True)
    managed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='managed_audit_request_actions',
        null=True,
        blank=True,
    )
    managed_at = models.DateTimeField(null=True, blank=True)
    occurred_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'audit_request_actions'
        ordering = ['-id']

    def __str__(self):
        """Return readable request action identifier."""
        return f'{self.app_scope}:{self.action_name}:{self.id}'


class AuditAlert(models.Model):
    """Real-time alert record derived from suspicious audit events."""

    event = models.ForeignKey(
        AuditEvent,
        on_delete=models.CASCADE,
        related_name='alerts',
    )
    alert_type = models.CharField(max_length=32, choices=AlertType.choices)
    severity = models.CharField(max_length=16, choices=AlertSeverity.choices, default=AlertSeverity.WARNING)
    description = models.CharField(max_length=255)
    context = models.JSONField(default=dict)
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='audit_alerts',
        null=True,
        blank=True,
    )
    triggered_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'audit_alerts'
        ordering = ['-triggered_at']

    def __str__(self):
        """Return readable alert summary."""
        return f'{self.get_alert_type_display()} -> {self.event}'
