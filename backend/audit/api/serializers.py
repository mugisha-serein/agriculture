"""Serializers for audit APIs."""

from rest_framework import serializers

from audit.domain.actions import AuditAction
from audit.domain.management import AuditManagementStatus
from audit.models import AuditEvent
from audit.models import AuditRequestAction


class AuditEventQuerySerializer(serializers.Serializer):
    """Query serializer for filtering audit events."""

    request_id = serializers.CharField(required=False)
    actor_id = serializers.IntegerField(required=False)
    action = serializers.ChoiceField(choices=AuditAction.choices, required=False)
    app_label = serializers.CharField(required=False)
    model_label = serializers.CharField(required=False)
    object_pk = serializers.CharField(required=False)
    page = serializers.IntegerField(min_value=1, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=200, default=50)


class AuditEventSerializer(serializers.ModelSerializer):
    """Output serializer for immutable audit event rows."""

    actor_id = serializers.IntegerField(source='actor.id', read_only=True, allow_null=True)

    class Meta:
        model = AuditEvent
        fields = (
            'id',
            'occurred_at',
            'request_id',
            'actor_id',
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
        )


class AuditRequestActionQuerySerializer(serializers.Serializer):
    """Query serializer for filtering request-level action logs."""

    request_id = serializers.CharField(required=False)
    actor_id = serializers.IntegerField(required=False)
    app_scope = serializers.ChoiceField(
        choices=['payments', 'orders', 'logistics', 'listings', 'verification', 'last_login'],
        required=False,
    )
    request_method = serializers.CharField(required=False)
    status_code = serializers.IntegerField(required=False)
    management_status = serializers.ChoiceField(
        choices=AuditManagementStatus.choices,
        required=False,
    )
    page = serializers.IntegerField(min_value=1, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=200, default=50)


class AuditRequestActionManageSerializer(serializers.Serializer):
    """Input serializer for managing request action status."""

    management_status = serializers.ChoiceField(choices=AuditManagementStatus.choices)
    management_note = serializers.CharField(required=False, allow_blank=True)


class AuditRequestActionSerializer(serializers.ModelSerializer):
    """Output serializer for request-level action logs."""

    actor_id = serializers.IntegerField(source='actor.id', read_only=True, allow_null=True)
    managed_by_id = serializers.IntegerField(source='managed_by.id', read_only=True, allow_null=True)

    class Meta:
        model = AuditRequestAction
        fields = (
            'id',
            'occurred_at',
            'request_id',
            'actor_id',
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
            'management_status',
            'management_note',
            'managed_by_id',
            'managed_at',
        )
