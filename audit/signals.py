from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from orders.models import Order
from products.models import Category, Product
from users.models import Coupon, UserProfile

from .middleware import get_current_request
from .models import AuditLog

TRACKED_MODELS = (User, UserProfile, Product, Category, Order, Coupon)
IGNORED_FIELDS = {"last_login", "updated_at"}   # noise, not a business change
SECRET_FIELDS = {"password"}                    # record *that* it changed, never the value


def _repr(instance):
    try:
        return str(instance)[:255]
    except Exception:
        return f"{instance.__class__.__name__} #{instance.pk}"


def _snapshot(instance):
    return {
        f.attname: getattr(instance, f.attname)
        for f in instance._meta.concrete_fields
        if f.name not in IGNORED_FIELDS
    }


# ---- Authentication events -------------------------------------------------
@receiver(user_logged_in)
def log_login(sender, request, user, **kwargs):
    AuditLog.record(AuditLog.Action.LOGIN_SUCCESS, request=request, user=user)


@receiver(user_logged_out)
def log_logout(sender, request, user, **kwargs):
    if user is not None:
        AuditLog.record(AuditLog.Action.LOGOUT, request=request, user=user)


@receiver(user_login_failed)
def log_login_failed(sender, credentials, request=None, **kwargs):
    attempted = (credentials.get("username") or credentials.get("email") or "")
    locked = bool(getattr(request, "_login_locked", False))
    AuditLog.record(
        AuditLog.Action.LOGIN_LOCKED if locked else AuditLog.Action.LOGIN_FAILED,
        request=request,
        username=str(attempted).lower(),
    )


# ---- Data-change events ----------------------------------------------------
@receiver(pre_save)
def remember_old_values(sender, instance, **kwargs):
    if sender not in TRACKED_MODELS or instance.pk is None:
        return
    old = sender._default_manager.filter(pk=instance.pk).first()
    instance._audit_old = _snapshot(old) if old else None


@receiver(post_save)
def log_save(sender, instance, created, **kwargs):
    if sender not in TRACKED_MODELS:
        return
    request = get_current_request()
    base = dict(object_type=sender.__name__, object_id=str(instance.pk), object_repr=_repr(instance))
    if created:
        AuditLog.record(AuditLog.Action.CREATE, request=request, **base)
        return
    old = getattr(instance, "_audit_old", None) or {}
    new = _snapshot(instance)
    changes = {}
    for field, new_value in new.items():
        if field in old and old[field] != new_value:
            changes[field] = "changed" if field in SECRET_FIELDS else [str(old[field]), str(new_value)]
    if changes:
        AuditLog.record(AuditLog.Action.UPDATE, request=request, changes=changes, **base)


@receiver(post_delete)
def log_delete(sender, instance, **kwargs):
    if sender not in TRACKED_MODELS:
        return
    AuditLog.record(
        AuditLog.Action.DELETE,
        request=get_current_request(),
        object_type=sender.__name__,
        object_id=str(instance.pk),
        object_repr=_repr(instance),
    )
