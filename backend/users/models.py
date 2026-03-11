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


class DeviceType(models.TextChoices):
    """Supported user device types."""

    WEB = 'web', 'Web'
    MOBILE = 'mobile', 'Mobile'
    TABLET = 'tablet', 'Tablet'
    DESKTOP = 'desktop', 'Desktop'
    OTHER = 'other', 'Other'


class LoginChallengeStatus(models.TextChoices):
    """Lifecycle statuses for login verification challenges."""

    PENDING = 'pending', 'Pending'
    VERIFIED = 'verified', 'Verified'
    EXPIRED = 'expired', 'Expired'
    FAILED = 'failed', 'Failed'


class IpReputationRisk(models.TextChoices):
    """Risk levels for IP reputation entries."""

    LOW = 'low', 'Low'
    MEDIUM = 'medium', 'Medium'
    HIGH = 'high', 'High'


class RateLimitScope(models.TextChoices):
    """Rate limit scopes for authentication endpoints."""

    IP = 'ip', 'IP'
    DEVICE = 'device', 'Device'
    USER = 'user', 'User'


class User(AbstractBaseUser, PermissionsMixin, TimestampedModel):
    """Identity entity representing platform users."""

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120, default="")
    phone = models.CharField(max_length=120, default="")
    role = models.CharField(max_length=32, choices=UserRole.choices, default=UserRole.BUYER)
    roles = models.ManyToManyField(
        'Role',
        through='UserRoleAssignment',
        related_name='users',
        blank=True,
    )
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


class Role(TimestampedModel):
    """Role definition for RBAC assignments."""

    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    permissions = models.ManyToManyField(
        'Permission',
        through='RolePermission',
        related_name='roles',
        blank=True,
    )

    class Meta:
        db_table = 'roles'
        ordering = ['code']

    def __str__(self):
        """Return a readable representation of the role."""
        return self.code


class Permission(TimestampedModel):
    """Permission definition for RBAC enforcement."""

    code = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'permissions'
        ordering = ['code']

    def __str__(self):
        """Return a readable representation of the permission."""
        return self.code


class RolePermission(TimestampedModel):
    """Join table linking roles to permissions."""

    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name='role_permissions',
    )

    class Meta:
        db_table = 'role_permissions'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['role', 'permission'],
                name='unique_role_permission',
            )
        ]

    def __str__(self):
        """Return a readable representation of the role permission link."""
        return f'{self.role.code}:{self.permission.code}'


class UserRoleAssignment(TimestampedModel):
    """Join table linking users to roles."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='role_assignments')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_assignments')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'user_roles'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'role'],
                name='unique_user_role',
            )
        ]

    def __str__(self):
        """Return a readable representation of the user role assignment."""
        return f'{self.user.email}:{self.role.code}'


class UserDevice(TimestampedModel):
    """Tracked device metadata for a user account."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    device_identifier = models.CharField(max_length=128)
    name = models.CharField(max_length=120, blank=True)
    device_type = models.CharField(max_length=32, choices=DeviceType.choices, default=DeviceType.OTHER)
    operating_system = models.CharField(max_length=120, blank=True)
    browser = models.CharField(max_length=120, blank=True)
    app_version = models.CharField(max_length=64, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    last_ip_address = models.GenericIPAddressField(null=True, blank=True)
    first_seen_at = models.DateTimeField(default=timezone.now)
    last_seen_at = models.DateTimeField(default=timezone.now)
    is_trusted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'user_devices'
        ordering = ['-last_seen_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'device_identifier'],
                name='unique_user_device_identifier',
            )
        ]

    def __str__(self):
        """Return a readable representation of the device."""
        return f'{self.user.email}:{self.device_identifier}'


class LoginVerificationChallenge(TimestampedModel):
    """Out-of-band challenge required for anomalous logins."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_challenges')
    challenge_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    device_identifier = models.CharField(max_length=128, blank=True)
    device_name = models.CharField(max_length=120, blank=True)
    device_type = models.CharField(max_length=32, choices=DeviceType.choices, default=DeviceType.OTHER)
    operating_system = models.CharField(max_length=120, blank=True)
    browser = models.CharField(max_length=120, blank=True)
    app_version = models.CharField(max_length=64, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    code_hash = models.CharField(max_length=64)
    debug_code = models.CharField(max_length=12, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=5)
    status = models.CharField(
        max_length=16,
        choices=LoginChallengeStatus.choices,
        default=LoginChallengeStatus.PENDING,
    )
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'login_verification_challenges'
        ordering = ['-created_at']

    def __str__(self):
        """Return a readable representation of the login challenge."""
        return f'{self.user.email}:{self.challenge_id}:{self.status}'


class LoginAttempt(TimestampedModel):
    """Track login attempts for brute-force protection."""

    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='login_attempts', null=True, blank=True)
    email = models.EmailField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    failed_count = models.PositiveSmallIntegerField(default=0)
    first_failed_at = models.DateTimeField(null=True, blank=True)
    last_failed_at = models.DateTimeField(null=True, blank=True)
    locked_until = models.DateTimeField(null=True, blank=True)
    last_failure_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'login_attempts'
        ordering = ['-last_failed_at']
        constraints = [
            models.UniqueConstraint(
                fields=['email', 'ip_address'],
                name='unique_login_attempt_per_email_ip',
            )
        ]

    def __str__(self):
        """Return a readable representation of the login attempt record."""
        return f'{self.email}:{self.ip_address or "unknown"}'


class LoginRateLimit(TimestampedModel):
    """Rate limit counters for login endpoints."""

    scope = models.CharField(max_length=16, choices=RateLimitScope.choices)
    key = models.CharField(max_length=191)
    action = models.CharField(max_length=32, default='login')
    window_started_at = models.DateTimeField(default=timezone.now)
    last_attempt_at = models.DateTimeField(default=timezone.now)
    attempt_count = models.PositiveIntegerField(default=0)
    blocked_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'login_rate_limits'
        ordering = ['-last_attempt_at']
        constraints = [
            models.UniqueConstraint(
                fields=['scope', 'key', 'action'],
                name='unique_login_rate_limit_scope_key_action',
            )
        ]

    def __str__(self):
        """Return a readable representation of the rate limit record."""
        return f'{self.scope}:{self.key}:{self.action}'


class IpReputation(TimestampedModel):
    """Reputation record for an IP address."""

    ip_address = models.GenericIPAddressField(unique=True)
    risk_level = models.CharField(max_length=16, choices=IpReputationRisk.choices, default=IpReputationRisk.LOW)
    source = models.CharField(max_length=64, blank=True)
    reason = models.TextField(blank=True)
    last_seen_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'ip_reputations'
        ordering = ['-last_seen_at']

    def __str__(self):
        """Return a readable representation of the IP reputation entry."""
        return f'{self.ip_address}:{self.risk_level}'


class UserSession(TimestampedModel):
    """User authentication session tracked by the identity app."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    device = models.ForeignKey(
        UserDevice,
        on_delete=models.SET_NULL,
        related_name='sessions',
        null=True,
        blank=True,
    )
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
