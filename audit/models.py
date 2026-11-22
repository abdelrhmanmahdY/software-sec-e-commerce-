
import logging

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

logger = logging.getLogger("audit")


class AuditLog(models.Model):
    """Append-only record of who did what, when, and from where."""

    class Action(models.TextChoices):
        LOGIN_SUCCESS = "login_success", "Login success"
        LOGIN_FAILED = "login_failed", "Login failed"
        LOGIN_LOCKED = "login_locked", "Login blocked (lockout)"

        TOTP_FAILED = "totp_failed", "TOTP verification failed"
        TOTP_LOCKED = "totp_locked", "TOTP verification blocked"

        LOGOUT = "logout", "Logout"
        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"
        ACCESS_DENIED = "access_denied", "Access denied (403)"

    timestamp = models.DateTimeField(
        default=timezone.now,
        db_index=True
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )

    # Actor's username, or attempted username for failed logins.
    username = models.CharField(
        max_length=150,
        blank=True,
        db_index=True
    )

    action = models.CharField(
        max_length=20,
        choices=Action.choices,
        db_index=True
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        db_index=True
    )

    user_agent = models.CharField(max_length=300, blank=True)
    method = models.CharField(max_length=10, blank=True)
    path = models.CharField(max_length=300, blank=True)
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)

    # {"field": [old, new]} for updates.
    # Sensitive fields must never contain their actual values.
    changes = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-timestamp", "-id"]
        indexes = [
            models.Index(
                fields=["action", "username", "ip_address", "timestamp"]
            )
        ]

    def __str__(self):
        return (
            f"{self.timestamp:%Y-%m-%d %H:%M:%S} "
            f"{self.action} {self.username or '-'}"
        )

    @classmethod
    def record(
        cls,
        action,
        *,
        request=None,
        user=None,
        username="",
        **fields
    ):
        """Write one audit entry. Never raises."""

        from .utils import get_client_ip

        try:
            if user is None and request is not None:
                candidate = getattr(request, "user", None)

                if (
                    candidate is not None
                    and getattr(candidate, "is_authenticated", False)
                ):
                    user = candidate

            if user is not None and not getattr(user, "pk", None):
                user = None

            if not username and user is not None:
                username = user.get_username()

            # Savepoint: audit failures must not poison caller transaction.
            with transaction.atomic():
                entry = cls.objects.create(
                    action=action,
                    user=user,
                    username=(username or "")[:150],
                    ip_address=(
                        get_client_ip(request)
                        if request is not None
                        else None
                    ),
                    user_agent=(
                        (request.META.get("HTTP_USER_AGENT") or "")[:300]
                        if request is not None
                        else ""
                    ),
                    method=(
                        request.method or ""
                        if request is not None
                        else ""
                    ),
                    path=(
                        request.get_full_path()[:300]
                        if request is not None
                        else ""
                    ),
                    **fields,
                )

            logger.info(
                "action=%s user=%s ip=%s object=%s:%s changes=%s",
                action,
                entry.username or "-",
                entry.ip_address or "-",
                entry.object_type or "-",
                entry.object_id or "-",
                entry.changes or "-",
            )

            return entry

        except Exception:
            logger.exception(
                "Failed to write audit log entry (action=%s)",
                action
            )
            return None


class AuthThrottle(models.Model):
    """
    Persistent brute-force protection for authentication.

    Stores hashed throttle keys instead of raw usernames or IP addresses.
    """

    key = models.CharField(
        max_length=64,
        unique=True
    )

    failures = models.PositiveIntegerField(default=0)

    window_started_at = models.DateTimeField(
        default=timezone.now
    )

    locked_until = models.DateTimeField(
        null=True,
        blank=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        indexes = [
            models.Index(fields=["locked_until"]),
        ]

    def __str__(self):
        return f"AuthThrottle {self.key[:12]}"
