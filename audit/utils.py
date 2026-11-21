from datetime import timedelta

from django.conf import settings
from django.db.models import Max
from django.utils import timezone


def get_client_ip(request):
    """Client IP. X-Forwarded-For is honoured only when TRUST_PROXY_HEADERS is on,
    i.e. when the app sits behind a proxy (nginx) that *overwrites* the header."""
    if request is None:
        return None
    if getattr(settings, "TRUST_PROXY_HEADERS", False):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded:
            return forwarded.split(",")[0].strip() or None
    return request.META.get("REMOTE_ADDR") or None


def is_locked_out(username, ip):
    """True when this username+IP pair (or the IP alone) has too many recent failures."""
    from .models import AuditLog

    max_failures = settings.LOGIN_MAX_FAILURES
    window_start = timezone.now() - timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
    failed = AuditLog.objects.filter(
        action__in=[AuditLog.Action.LOGIN_FAILED, AuditLog.Action.LOGIN_LOCKED],
        timestamp__gte=window_start,
    )

    if username:
        pair = failed.filter(username__iexact=username, ip_address=ip)
        last_ok = AuditLog.objects.filter(
            action=AuditLog.Action.LOGIN_SUCCESS,
            username__iexact=username,
            ip_address=ip,
            timestamp__gte=window_start,
        ).aggregate(t=Max("timestamp"))["t"]
        if last_ok:
            pair = pair.filter(timestamp__gt=last_ok)
        if pair.count() >= max_failures:
            return True

    # Spraying many usernames from one address.
    if ip and failed.filter(ip_address=ip).count() >= settings.LOGIN_MAX_FAILURES_PER_IP:
        return True
    return False
