from contextvars import ContextVar

from .models import AuditLog

_current_request = ContextVar("audit_current_request", default=None)


def get_current_request():
    return _current_request.get()


class AuditMiddleware:
    """Makes the current request available to model signals (so we know *who*
    changed a row) and records authorization failures (HTTP 403)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = _current_request.set(request)
        try:
            response = self.get_response(request)
            if response.status_code == 403:
                AuditLog.record(AuditLog.Action.ACCESS_DENIED, request=request)
            return response
        finally:
            _current_request.reset(token)
