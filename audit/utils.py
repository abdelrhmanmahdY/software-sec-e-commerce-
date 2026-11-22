
import hashlib
import hmac

from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Max
from django.utils import timezone


def get_client_ip(request):
    """Get client IP safely behind a trusted reverse proxy."""

    if request is None:
        return None

    if getattr(settings, "TRUST_PROXY_HEADERS", False):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")

        if forwarded:
            return forwarded.split(",")[0].strip() or None

    return request.META.get("REMOTE_ADDR") or None


def is_locked_out(username, ip):
    """Check existing login lockout protection."""

    from .models import AuditLog

    max_failures = settings.LOGIN_MAX_FAILURES

    window_start = timezone.now() - timedelta(
        minutes=settings.LOGIN_LOCKOUT_MINUTES
    )

    failed = AuditLog.objects.filter(
        action__in=[
            AuditLog.Action.LOGIN_FAILED,
            AuditLog.Action.LOGIN_LOCKED,
        ],
        timestamp__gte=window_start,
    )

    if username:
        pair = failed.filter(
            username__iexact=username,
            ip_address=ip,
        )

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

    if ip and failed.filter(
        ip_address=ip
    ).count() >= settings.LOGIN_MAX_FAILURES_PER_IP:
        return True

    return False


def _get_throttle_key(scope, identity):
    """Generate a non-reversible HMAC throttle identifier."""

    if identity is None:
        return None

    identity = str(identity).strip().lower()

    if not identity:
        return None

    message = f"{scope}:{identity}".encode("utf-8")
    secret = str(settings.SECRET_KEY).encode("utf-8")

    return hmac.new(
        secret,
        message,
        hashlib.sha256,
    ).hexdigest()


def is_throttled(scope, identity):
    """Check whether an identity is currently locked."""

    from .models import AuthThrottle

    key = _get_throttle_key(scope, identity)

    if not key:
        return False

    return AuthThrottle.objects.filter(
        key=key,
        locked_until__gt=timezone.now(),
    ).exists()


def record_throttle_failure(
    scope,
    identity,
    max_failures=5,
    window_minutes=10,
    lockout_minutes=10,
):
    """Record a failed attempt with atomic database protection."""

    from .models import AuthThrottle

    key = _get_throttle_key(scope, identity)

    if not key:
        return {"locked": False, "failures": 0}

    now = timezone.now()

    with transaction.atomic():

        record, created = (
            AuthThrottle.objects
            .select_for_update()
            .get_or_create(key=key)
        )

        if record.locked_until and record.locked_until > now:
            return {
                "locked": True,
                "failures": record.failures,
                "locked_until": record.locked_until,
            }

        window_expired = (
            record.window_started_at
            <= now - timedelta(minutes=window_minutes)
        )

        lock_expired = (
            record.locked_until is not None
            and record.locked_until <= now
        )

        if window_expired or lock_expired:

            record.failures = 0
            record.window_started_at = now
            record.locked_until = None

        record.failures += 1

        if record.failures >= max_failures:
            record.locked_until = (
                now + timedelta(minutes=lockout_minutes)
            )

        record.save(
            update_fields=[
                "failures",
                "window_started_at",
                "locked_until",
                "updated_at",
            ]
        )

        return {
            "locked": record.locked_until is not None,
            "failures": record.failures,
            "locked_until": record.locked_until,
        }


def clear_throttle(scope, identity):
    """Reset an identity's failed-attempt counter."""

    from .models import AuthThrottle

    key = _get_throttle_key(scope, identity)

    if not key:
        return

    with transaction.atomic():

        record = (
            AuthThrottle.objects
            .select_for_update()
            .filter(key=key)
            .first()
        )

        if record:
            record.failures = 0
            record.window_started_at = timezone.now()
            record.locked_until = None

            record.save(
                update_fields=[
                    "failures",
                    "window_started_at",
                    "locked_until",
                    "updated_at",
                ]
            )


def is_totp_locked_out(user_id, ip):
    """Check TOTP account-level and IP-level lockouts."""

    return (
        is_throttled("totp_user", user_id)
        or is_throttled("totp_ip", ip)
    )


def record_totp_failure(user_id, ip):
    """Record TOTP failure against both account and IP."""

    user_result = record_throttle_failure(
        scope="totp_user",
        identity=user_id,
        max_failures=5,
        window_minutes=10,
        lockout_minutes=10,
    )

    ip_result = record_throttle_failure(
        scope="totp_ip",
        identity=ip,
        max_failures=20,
        window_minutes=10,
        lockout_minutes=10,
    )

    return {
        "locked": (
            user_result["locked"]
            or ip_result["locked"]
        ),
        "user": user_result,
        "ip": ip_result,
    }


def clear_totp_throttle(user_id, ip):
    """Clear TOTP failures after successful authentication."""

    clear_throttle("totp_user", user_id)
    clear_throttle("totp_ip", ip)
