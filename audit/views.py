from rest_framework import status
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from django.conf import settings

from .models import AuditLog
from .utils import (
    clear_throttle,
    get_client_ip,
    is_locked_out,
    is_totp_locked_out,
    record_totp_failure,
)
from users.models import UserProfile
from users.totp import consume_totp_code


class TotpTokenObtainPairSerializer(TokenObtainPairSerializer):
    totp_code = serializers.CharField(required=False, allow_blank=True, write_only=True)

    def validate(self, attrs):
        data = super().validate(attrs)
        profile = UserProfile.objects.filter(user=self.user).first()
        if not profile or not profile.totp_enabled:
            return data

        request = self.context.get("request")
        ip_address = get_client_ip(request)
        if is_totp_locked_out(self.user.pk, ip_address):
            AuditLog.record(
                AuditLog.Action.TOTP_LOCKED,
                request=request,
                user=self.user,
                object_type="UserProfile",
                object_id=str(profile.pk),
                object_repr=str(profile),
                changes={"reason": "TOTP lockout active"},
            )
            raise AuthenticationFailed("Invalid credentials.")

        code = attrs.get("totp_code", "")
        if not consume_totp_code(profile, code, require_enabled=True):
            result = record_totp_failure(self.user.pk, ip_address)
            AuditLog.record(
                AuditLog.Action.TOTP_FAILED,
                request=request,
                user=self.user,
                object_type="UserProfile",
                object_id=str(profile.pk),
                object_repr=str(profile),
                changes={
                    "user_failures": result["user"]["failures"],
                    "ip_failures": result["ip"]["failures"],
                },
            )
            raise AuthenticationFailed("Invalid credentials.")

        clear_throttle("totp_user", self.user.pk)
        return data


class AuditedTokenObtainPairView(TokenObtainPairView):
    """POST /api/auth/login/ - JWT login with lockout (429) and audit logging."""
    serializer_class = TotpTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        username = str(request.data.get("username", "")).lower()
        if username and is_locked_out(username, get_client_ip(request)):
            AuditLog.record(AuditLog.Action.LOGIN_LOCKED, request=request, username=username)
            response = Response(
                {"detail": "Too many failed attempts. Try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
            response["Retry-After"] = str(settings.LOGIN_LOCKOUT_MINUTES * 60)
            return response
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:   # failures are logged by the user_login_failed signal
            AuditLog.record(AuditLog.Action.LOGIN_SUCCESS, request=request, username=username)
        return response


class LogoutAPIView(APIView):
    """POST /api/auth/logout/ {"refresh": "<token>"} - revokes the refresh token."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            RefreshToken(request.data.get("refresh", "")).blacklist()
        except TokenError:
            return Response({"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
        AuditLog.record(AuditLog.Action.LOGOUT, request=request)
        return Response(status=status.HTTP_205_RESET_CONTENT)
