"""Middleware for audit context capture and request correlation ids."""

from time import perf_counter
from uuid import uuid4

from audit.context import reset_request_context
from audit.context import set_request_context
from audit.services.audit_service import AuditService


class AuditContextMiddleware:
    """Capture request metadata for downstream audit event generation."""

    def __init__(self, get_response):
        """Initialize middleware with downstream callable."""
        self.get_response = get_response

    def __call__(self, request):
        """Store request context, invoke downstream stack, and restore state."""
        request_id = request.headers.get('X-Request-ID') or str(uuid4())
        request.audit_request_id = request_id
        start = perf_counter()
        request_token, request_id_token = set_request_context(
            request=request,
            request_id=request_id,
        )
        try:
            response = self.get_response(request)
            exception_name = ''
        except Exception as exc:
            response = None
            exception_name = exc.__class__.__name__
            raise
        finally:
            duration_ms = int((perf_counter() - start) * 1000)
            try:
                audit_service = AuditService()
                if response is not None:
                    response_payload = self._extract_response_payload(response=response)
                    audit_service.record_request_action(
                        request=request,
                        response_status_code=response.status_code,
                        duration_ms=duration_ms,
                        response_data=response_payload,
                    )
                else:
                    audit_service.record_request_action(
                        request=request,
                        response_status_code=500,
                        duration_ms=duration_ms,
                        response_data={},
                        exception_name=exception_name,
                    )
            except Exception:
                pass
            reset_request_context(request_token=request_token, request_id_token=request_id_token)
        response['X-Request-ID'] = request_id
        return response

    def _extract_response_payload(self, *, response):
        """Extract JSON-safe response payload for audit storage."""
        data = getattr(response, 'data', None)
        if data is None:
            return {}
        if isinstance(data, dict):
            return data
        if isinstance(data, list):
            return {'items': data}
        return {'value': str(data)}
