
# from api.serializers.se_register import (
#     RegisterSerializer,
# )
# from rest_framework import status
from datetime import timedelta
from math import ceil

from api.audit import log_event
from api.models import User
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

MAX_FAILED_ATTEMPTS = 5
LOCK_DURATION = timedelta(minutes=30)


class LockoutTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        user = User.objects.filter(username=attrs.get("username")).first()

        username = attrs.get("username")

        if user and user.locked_until:
            if user.locked_until > timezone.now():
                remaining = ceil((user.locked_until - timezone.now()).total_seconds() / 60)
                log_event("authentication", "login", "failure", username=username, reason="account_locked")
                raise AuthenticationFailed(
                    f"Tài khoản đã bị tạm khóa do đăng nhập sai quá {MAX_FAILED_ATTEMPTS} lần. "
                    f"Vui lòng thử lại sau {remaining} phút."
                )
            user.locked_until = None
            user.failed_login_attempts = 0
            user.save(update_fields=["locked_until", "failed_login_attempts"])

        try:
            data = super().validate(attrs)
        except AuthenticationFailed:
            if not user:
                log_event("authentication", "login", "failure", username=username, reason="unknown_user")
                raise
            if not user.is_active:
                log_event("authentication", "login", "failure", username=username, reason="inactive")
                raise AuthenticationFailed(
                    "Tài khoản của bạn đã bị khóa. Vui lòng liên hệ quản trị viên."
                )

            user.failed_login_attempts += 1
            if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                user.locked_until = timezone.now() + LOCK_DURATION
                user.failed_login_attempts = 0
                user.save(update_fields=["failed_login_attempts", "locked_until"])
                log_event("authentication", "account_locked", "failure", username=username)
                raise AuthenticationFailed(
                    f"Bạn đã nhập sai mật khẩu quá {MAX_FAILED_ATTEMPTS} lần. "
                    f"Tài khoản đã bị tạm khóa trong 30 phút."
                )

            user.save(update_fields=["failed_login_attempts"])
            remaining_attempts = MAX_FAILED_ATTEMPTS - user.failed_login_attempts
            log_event(
                "authentication", "login", "failure",
                username=username, reason="bad_password", remaining_attempts=remaining_attempts,
            )
            raise AuthenticationFailed(
                f"Sai tên đăng nhập hoặc mật khẩu. Còn {remaining_attempts} lần thử trước khi bị khóa."
            )

        user.failed_login_attempts = 0
        user.save(update_fields=["failed_login_attempts"])
        log_event("authentication", "login", "success", username=username)
        return data


class LockoutTokenObtainPairView(TokenObtainPairView):
    serializer_class = LockoutTokenObtainPairSerializer


class LoggingTokenRefreshView(TokenRefreshView):
    """TOKEN_REFRESH audit event - simplejwt's view has no hook, so wrap post()."""

    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
        except Exception:
            log_event("authentication", "token_refresh", "failure")
            raise
        log_event("authentication", "token_refresh", "success")
        return response


class LoginCheck(APIView):
    authentication_classes = [JWTAuthentication]  # noqa: RUF012
    permission_classes = [IsAuthenticated]  # noqa: RUF012
    
    def get(self, request):
        name = request.user.name
        email = request.user.email
        role = request.user.role

        data = {
            'name': name,
            'email': email,
            'role': role,
        }
        return Response(data)
