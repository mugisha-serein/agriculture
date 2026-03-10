"""Admin registrations for audit models."""

from django.contrib import admin

from audit.models import AuditEvent
from audit.models import AuditRequestAction


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    """Admin configuration for immutable audit events."""

    list_display = (
        'id',
        'occurred_at',
        'action',
        'model_label',
        'object_pk',
        'actor_email',
        'request_id',
    )
    list_filter = ('action', 'app_label', 'model_label')
    search_fields = (
        'request_id',
        'model_label',
        'object_pk',
        'actor_email',
        'request_path',
    )
    ordering = ('-id',)
    readonly_fields = (
        'request_id',
        'actor',
        'actor_email',
        'source',
        'action',
        'app_label',
        'model_label',
        'object_pk',
        'object_repr',
        'request_path',
        'request_method',
        'ip_address',
        'user_agent',
        'before_state',
        'after_state',
        'change_set',
        'metadata',
        'previous_hash',
        'event_hash',
        'occurred_at',
    )

    def has_add_permission(self, request):
        """Disable manual creation of audit events in admin."""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable manual edits of audit events in admin."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Disable deletion of audit events in admin."""
        return False


@admin.register(AuditRequestAction)
class AuditRequestActionAdmin(admin.ModelAdmin):
    """Admin configuration for request-level audit actions."""

    list_display = (
        'id',
        'occurred_at',
        'app_scope',
        'action_name',
        'request_method',
        'status_code',
        'actor_email',
        'management_status',
    )
    list_filter = ('app_scope', 'request_method', 'status_code', 'management_status')
    search_fields = ('request_id', 'action_name', 'request_path', 'actor_email')
    ordering = ('-id',)
    readonly_fields = (
        'request_id',
        'actor',
        'actor_email',
        'app_scope',
        'action_name',
        'request_path',
        'request_method',
        'status_code',
        'succeeded',
        'ip_address',
        'user_agent',
        'query_params',
        'request_data',
        'response_data',
        'metadata',
        'duration_ms',
        'previous_hash',
        'event_hash',
        'occurred_at',
    )
