"""Authorization helpers shared by the dashboard (session) views and the REST API."""
from functools import wraps

from django.core.exceptions import PermissionDenied
from rest_framework.permissions import SAFE_METHODS, BasePermission


def staff_required(view):
    """Use *after* @login_required. Logged-in non-staff get a real 403
    (which the audit middleware records) instead of a redirect loop."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapper


class IsStaff(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsStaffOrCreateReadOnly(BasePermission):
    """Any authenticated user may read (own data) and create; only staff may modify/delete."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in SAFE_METHODS or request.method == "POST":
            return True
        return user.is_staff
