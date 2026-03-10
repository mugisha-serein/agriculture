"""Identity data models for users, sessions, and refresh tokens."""

import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from users.domain.roles import UserRole
from users.managers import UserManager


class TimestampedModel(models.Model):
    """Abstract base model with created and updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(AbstractBaseUser, PermissionsMixin, TimestampedModel):
    """Identity entity representing platform users."""

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120, default="")
    phone = models.CharField(max_length=120, default="")
    role = models.CharField(max_length=32, choices=UserRole.choices, default=UserRole.BUYER)
    is_active = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    activated_at = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role']

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self):
        """Return a readable representation of the user."""
        return self.email


class UserSession(TimestampedModel):
    """User authentication session tracked by the identity app."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    user_agent = models.CharField(max_length=512, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    started_at = models.DateTimeField(default=timezone.now)
    last_seen_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'sessions'
        ordering = ['-started_at']

    def __str__(self):
        """Return a readable representation of the session."""
        return f'{self.user.email}:{self.id}'


class RefreshToken(TimestampedModel):
    """Refresh token registry used for revocation and rotation controls."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refresh_tokens')
    session = models.ForeignKey(UserSession, on_delete=models.CASCADE, related_name='refresh_tokens')
    jti = models.UUIDField(default=uuid.uuid4, unique=True)
    token_hash = models.CharField(max_length=64, unique=True)
    issued_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'refresh_tokens'
        ordering = ['-issued_at']

    def __str__(self):
        """Return a readable representation of the refresh token."""
        return f'{self.user.email}:{self.jti}'
