"""Serializers for identity API endpoints."""

from rest_framework import serializers

from users.domain.roles import UserRole
from users.models import DeviceType


class RegistrationSerializer(serializers.Serializer):
    """Input serializer for registration requests."""

    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=120)
    last_name = serializers.CharField(max_length=120)
    phone = serializers.CharField(max_length=120)
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=UserRole.choices, default=UserRole.BUYER)


class ActivationSerializer(serializers.Serializer):
    """Input serializer for account activation."""

    token = serializers.CharField()


class LoginSerializer(serializers.Serializer):
    """Input serializer for login requests."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    user_agent = serializers.CharField(max_length=512, required=False, allow_blank=True)
    device_id = serializers.CharField(max_length=128, required=False, allow_blank=True)
    device_name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    device_type = serializers.ChoiceField(choices=DeviceType.choices, required=False, allow_blank=True)
    device_os = serializers.CharField(max_length=120, required=False, allow_blank=True)
    device_browser = serializers.CharField(max_length=120, required=False, allow_blank=True)
    app_version = serializers.CharField(max_length=64, required=False, allow_blank=True)


class RefreshSerializer(serializers.Serializer):
    """Input serializer for refresh token requests."""

    refresh_token = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    """Input serializer for logout requests."""

    refresh_token = serializers.CharField()


class TokenVerifySerializer(serializers.Serializer):
    """Input serializer for access token verification."""

    access_token = serializers.CharField()


class LoginVerificationSerializer(serializers.Serializer):
    """Input serializer for login verification challenges."""

    challenge_id = serializers.UUIDField()
    verification_code = serializers.CharField(max_length=12)
    user_agent = serializers.CharField(max_length=512, required=False, allow_blank=True)
