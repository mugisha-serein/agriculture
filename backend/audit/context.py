"""Request context helpers for audit metadata propagation."""

from contextvars import ContextVar


_request_var = ContextVar('audit_request', default=None)
_request_id_var = ContextVar('audit_request_id', default='')


def set_request_context(*, request, request_id):
    """Set current request context and return context tokens."""
    request_token = _request_var.set(request)
    request_id_token = _request_id_var.set(request_id)
    return request_token, request_id_token


def reset_request_context(*, request_token, request_id_token):
    """Reset request context using provided tokens."""
    _request_var.reset(request_token)
    _request_id_var.reset(request_id_token)


def get_current_request():
    """Return current request object from context."""
    return _request_var.get()


def get_current_request_id():
    """Return current request identifier from context."""
    return _request_id_var.get()
