from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import PermissionDenied

from .utils import get_client_ip, is_locked_out


class LockoutModelBackend(ModelBackend):
    """ModelBackend that refuses to even check the password while the
    username+IP is locked out. Covers dashboard login, /admin/ and the JWT endpoint."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if request is not None and username:
            if is_locked_out(username, get_client_ip(request)):
                request._login_locked = True
                raise PermissionDenied("Too many failed login attempts.")
        return super().authenticate(request, username=username, password=password, **kwargs)
