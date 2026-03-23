"""Signal handlers for automatic model mutation auditing."""

from contextvars import ContextVar

from django.db.models.signals import post_delete
from django.db.models.signals import post_save
from django.db.models.signals import pre_delete
from django.db.models.signals import pre_save
from django.dispatch import receiver

from django.conf import settings

from audit.domain.actions import AuditAction
from audit.services.audit_service import AuditService


_before_update_state_var = ContextVar('audit_before_update_state', default={})
_before_delete_state_var = ContextVar('audit_before_delete_state', default={})

DEFAULT_AUDITED_APP_LABELS = {
    'verification',
    'listings',
    'orders',
    'payments',
    'logistics',
    'discovery',
    'reputation',
}


def _build_audited_app_labels():
    return set(getattr(settings, 'AUDIT_ENABLED_APPS', DEFAULT_AUDITED_APP_LABELS))


def _should_audit_sender(sender):
    """Return whether sender model should be audited."""
    app_label = sender._meta.app_label
    if app_label not in _build_audited_app_labels():
        if sender._meta.label != 'users.User':
            return False
    return True


@receiver(pre_save)
def capture_pre_save_state(sender, instance, raw=False, **kwargs):
    """Capture model state before update for change-set generation."""
    if raw:
        return
    if not _should_audit_sender(sender):
        return
    if instance.pk is None:
        return
    existing = sender.objects.filter(pk=instance.pk).first()
    if existing is None:
        return
    audit_service = AuditService()
    before_state = audit_service.serialize_instance(existing)
    state_map = dict(_before_update_state_var.get())
    state_map[id(instance)] = before_state
    _before_update_state_var.set(state_map)


@receiver(post_save)
def audit_post_save(sender, instance, created, raw=False, **kwargs):
    """Record immutable audit event after create or update operations."""
    if raw:
        return
    if not _should_audit_sender(sender):
        return
    audit_service = AuditService()
    if created:
        before_state = {}
        action = AuditAction.CREATE
    else:
        state_map = dict(_before_update_state_var.get())
        before_state = state_map.pop(id(instance), {})
        _before_update_state_var.set(state_map)
        action = AuditAction.UPDATE
    after_state = audit_service.serialize_instance(instance)
    source = 'model_signal'
    metadata = {}
    if sender._meta.label == 'users.User':
        if created:
            return
        change_set = audit_service._build_change_set(before_state=before_state, after_state=after_state)
        relevant_fields = {'last_login', 'role', 'is_staff', 'is_active'}
        changed_fields = set(change_set.keys())
        if not (changed_fields & relevant_fields):
            return
        action = AuditAction.UPDATE if not change_set.get('last_login') else AuditAction.CUSTOM
        if 'last_login' in change_set:
            source = 'last_login'
            metadata = {'action_name': 'last_login'}
    audit_service.record_model_event(
        action=action,
        instance=instance,
        before_state=before_state,
        after_state=after_state,
        source=source,
        metadata=metadata,
    )


@receiver(pre_delete)
def capture_pre_delete_state(sender, instance, **kwargs):
    """Capture model state before deletion for delete audit event."""
    if not _should_audit_sender(sender):
        return
    if sender._meta.label == 'users.User':
        return
    audit_service = AuditService()
    before_state = audit_service.serialize_instance(instance)
    state_map = dict(_before_delete_state_var.get())
    state_map[id(instance)] = before_state
    _before_delete_state_var.set(state_map)


@receiver(post_delete)
def audit_post_delete(sender, instance, **kwargs):
    """Record immutable delete audit event after model deletion."""
    if not _should_audit_sender(sender):
        return
    if sender._meta.label == 'users.User':
        return
    state_map = dict(_before_delete_state_var.get())
    before_state = state_map.pop(id(instance), {})
    _before_delete_state_var.set(state_map)
    audit_service = AuditService()
    audit_service.record_model_event(
        action=AuditAction.DELETE,
        instance=instance,
        before_state=before_state,
        after_state={},
    )
