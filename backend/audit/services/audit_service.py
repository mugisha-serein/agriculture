"""Audit service for immutable event creation and model state serialization."""

from datetime import date
from datetime import datetime
from datetime import time
from decimal import Decimal
import hashlib
import json
from uuid import UUID

from django.db import transaction
from django.http import QueryDict
from django.contrib.auth import get_user_model

from audit.context import get_current_request
from audit.context import get_current_request_id
from audit.models import AuditEvent
from audit.models import AuditRequestAction


class AuditService:
    """Application service for writing immutable audit events."""

    audited_request_prefixes = {
        '/api/payments/': 'payments',
        '/api/orders/': 'orders',
        '/api/logistics/': 'logistics',
        '/api/marketplace/': 'listings',
        '/api/verification/': 'verification',
        '/api/identity/login/': 'last_login',
    }

    @transaction.atomic
    def record_model_event(
        self,
        *,
        action,
        instance,
        before_state=None,
        after_state=None,
        source='model_signal',
        metadata=None,
    ):
        """Record model mutation event with request metadata and hash chain."""
        before_state = before_state or {}
        after_state = after_state or {}
        change_set = self._build_change_set(before_state=before_state, after_state=after_state)
        request = get_current_request()
        actor = self._resolve_actor(request=request)
        previous_hash = self._previous_event_hash()
        payload = {
            'request_id': get_current_request_id(),
            'actor_id': getattr(actor, 'id', None),
            'actor_email': getattr(actor, 'email', ''),
            'source': source,
            'action': action,
            'app_label': instance._meta.app_label,
            'model_label': instance._meta.label,
            'object_pk': str(instance.pk),
            'object_repr': str(instance),
            'request_path': getattr(request, 'path', ''),
            'request_method': getattr(request, 'method', ''),
            'ip_address': self._resolve_ip_address(request=request),
            'user_agent': self._resolve_user_agent(request=request),
            'before_state': before_state,
            'after_state': after_state,
            'change_set': change_set,
            'metadata': metadata or {},
            'previous_hash': previous_hash,
        }
        event_hash = self._compute_event_hash(payload=payload)
        return AuditEvent.objects.create(
            request_id=payload['request_id'],
            actor=actor,
            actor_email=payload['actor_email'],
            source=payload['source'],
            action=payload['action'],
            app_label=payload['app_label'],
            model_label=payload['model_label'],
            object_pk=payload['object_pk'],
            object_repr=payload['object_repr'],
            request_path=payload['request_path'],
            request_method=payload['request_method'],
            ip_address=payload['ip_address'],
            user_agent=payload['user_agent'],
            before_state=payload['before_state'],
            after_state=payload['after_state'],
            change_set=payload['change_set'],
            metadata=payload['metadata'],
            previous_hash=payload['previous_hash'],
            event_hash=event_hash,
        )

    def serialize_instance(self, instance):
        """Serialize model instance into JSON-safe state mapping."""
        state = {}
        for field in instance._meta.concrete_fields:
            value = getattr(instance, field.attname)
            state[field.attname] = self._normalize_value(value)
        return state

    @transaction.atomic
    def record_request_action(
        self,
        *,
        request,
        response_status_code,
        duration_ms,
        response_data=None,
        exception_name='',
    ):
        """Record request-level action for monitored app scopes."""
        app_scope = self._resolve_request_app_scope(path=request.path)
        if app_scope is None:
            return None
        actor = self._resolve_actor(request=request)
        response_payload = self._normalize_mapping(response_data or {})
        if actor is None and app_scope == 'last_login' and int(response_status_code) < 400:
            actor = self._resolve_login_actor(response_data=response_payload)
        action_name = self._resolve_action_name(request=request, app_scope=app_scope)
        payload = {
            'request_id': get_current_request_id(),
            'actor_id': getattr(actor, 'id', None),
            'actor_email': getattr(actor, 'email', ''),
            'app_scope': app_scope,
            'action_name': action_name,
            'request_path': request.path,
            'request_method': request.method,
            'status_code': int(response_status_code),
            'succeeded': int(response_status_code) < 400,
            'ip_address': self._resolve_ip_address(request=request),
            'user_agent': self._resolve_user_agent(request=request),
            'query_params': self._normalize_query_params(request.GET),
            'request_data': self._extract_request_data(request=request),
            'response_data': response_payload,
            'metadata': {'exception_name': exception_name} if exception_name else {},
            'duration_ms': int(duration_ms),
            'previous_hash': self._previous_request_action_hash(),
        }
        payload_for_hash = {
            key: value
            for key, value in payload.items()
            if key not in {'management_status', 'management_note', 'managed_by', 'managed_at'}
        }
        event_hash = self._compute_event_hash(payload=payload_for_hash)
        return AuditRequestAction.objects.create(
            request_id=payload['request_id'],
            actor=actor,
            actor_email=payload['actor_email'],
            app_scope=payload['app_scope'],
            action_name=payload['action_name'],
            request_path=payload['request_path'],
            request_method=payload['request_method'],
            status_code=payload['status_code'],
            succeeded=payload['succeeded'],
            ip_address=payload['ip_address'],
            user_agent=payload['user_agent'],
            query_params=payload['query_params'],
            request_data=payload['request_data'],
            response_data=payload['response_data'],
            metadata=payload['metadata'],
            duration_ms=payload['duration_ms'],
            previous_hash=payload['previous_hash'],
            event_hash=event_hash,
        )

    def _build_change_set(self, *, before_state, after_state):
        """Build changed field map between two serialized states."""
        if not before_state and after_state:
            return {
                field: {'from': None, 'to': value}
                for field, value in after_state.items()
            }
        if before_state and not after_state:
            return {
                field: {'from': value, 'to': None}
                for field, value in before_state.items()
            }
        change_set = {}
        all_keys = set(before_state.keys()) | set(after_state.keys())
        for key in sorted(all_keys):
            old_value = before_state.get(key)
            new_value = after_state.get(key)
            if old_value != new_value:
                change_set[key] = {'from': old_value, 'to': new_value}
        return change_set

    def _normalize_value(self, value):
        """Normalize python values for JSON storage."""
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, (datetime, date, time)):
            return value.isoformat()
        if hasattr(value, 'name'):
            return getattr(value, 'name', '')
        return str(value)

    def _normalize_mapping(self, mapping):
        """Normalize mapping into JSON-safe primitive dictionary."""
        if isinstance(mapping, QueryDict):
            return {key: mapping.getlist(key) if len(mapping.getlist(key)) > 1 else mapping.get(key) for key in mapping.keys()}
        if isinstance(mapping, dict):
            normalized = {}
            for key, value in mapping.items():
                normalized[str(key)] = self._normalize_nested(value)
            return normalized
        return {'value': self._normalize_nested(mapping)}

    def _normalize_nested(self, value):
        """Normalize nested values recursively for JSON serialization."""
        if isinstance(value, dict):
            return {str(k): self._normalize_nested(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._normalize_nested(item) for item in value]
        return self._normalize_value(value)

    def _normalize_query_params(self, query_dict):
        """Normalize query parameters into JSON-safe dictionary."""
        result = {}
        for key in query_dict.keys():
            values = query_dict.getlist(key)
            if len(values) == 1:
                result[key] = values[0]
            else:
                result[key] = values
        return result

    def _extract_request_data(self, *, request):
        """Extract request payload in JSON-safe format."""
        if request.method not in {'POST', 'PUT', 'PATCH', 'DELETE'}:
            return {}
        content_type = (request.META.get('CONTENT_TYPE') or '').lower()
        if 'application/json' in content_type:
            try:
                raw = request.body.decode('utf-8').strip()
                if not raw:
                    return {}
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    return self._normalize_mapping(parsed)
                return {'value': self._normalize_nested(parsed)}
            except Exception:
                return {}
        if hasattr(request, 'POST'):
            return self._normalize_mapping(request.POST)
        return {}

    def _resolve_actor(self, *, request):
        """Resolve authenticated actor from current request context."""
        if request is None:
            return None
        user = getattr(request, 'user', None)
        if user is None:
            return None
        if getattr(user, 'is_authenticated', False):
            return user
        return None

    def _resolve_ip_address(self, *, request):
        """Resolve client IP address from request metadata."""
        if request is None:
            return None
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded:
            return forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    def _resolve_user_agent(self, *, request):
        """Resolve request user agent string."""
        if request is None:
            return ''
        return request.META.get('HTTP_USER_AGENT', '')

    def _previous_event_hash(self):
        """Return hash of latest audit event for chain linking."""
        latest = AuditEvent.objects.order_by('-id').values('event_hash').first()
        if latest is None:
            return ''
        return latest['event_hash']

    def _previous_request_action_hash(self):
        """Return hash of latest request action for hash-chain linking."""
        latest = AuditRequestAction.objects.order_by('-id').values('event_hash').first()
        if latest is None:
            return ''
        return latest['event_hash']

    def _resolve_request_app_scope(self, *, path):
        """Resolve monitored app scope from request path."""
        for prefix, scope in self.audited_request_prefixes.items():
            if path.startswith(prefix):
                return scope
        return None

    def _resolve_action_name(self, *, request, app_scope):
        """Resolve action name from route or scope-specific defaults."""
        if app_scope == 'last_login':
            return 'last_login'
        resolver_match = getattr(request, 'resolver_match', None)
        if resolver_match and resolver_match.url_name:
            return resolver_match.url_name
        return request.method.lower()

    def _resolve_login_actor(self, *, response_data):
        """Resolve actor from successful login response payload."""
        user_payload = response_data.get('user')
        if not isinstance(user_payload, dict):
            return None
        user_id = user_payload.get('id')
        if user_id is None:
            return None
        User = get_user_model()
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    def _compute_event_hash(self, *, payload):
        """Compute deterministic hash for event payload integrity."""
        serialized = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()
