"""Admin registrations for identity models."""

from django.contrib import admin

from users.models import (
    IpReputation,
    LoginAttempt,
    LoginRateLimit,
    LoginVerificationChallenge,
    Permission,
    RefreshToken,
    Role,
    RolePermission,
    User,
    UserDevice,
    UserRoleAssignment,
    UserSession,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Admin configuration for users."""

    list_display = (
        'id',
        'email',
        'first_name',
        'last_name',
        'phone',
        'role',
        'is_active',
        'is_staff',
        'created_at',
    )
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('-created_at',)


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """Admin configuration for sessions."""

    list_display = ('id', 'user', 'device', 'ip_address', 'started_at', 'expires_at', 'revoked_at')
    list_filter = ('revoked_at',)
    search_fields = ('user__email', 'ip_address', 'user_agent', 'device__device_identifier')
    ordering = ('-started_at',)


@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    """Admin configuration for user devices."""

    list_display = ('id', 'user', 'device_identifier', 'device_type', 'last_seen_at', 'is_trusted', 'is_active')
    list_filter = ('device_type', 'is_trusted', 'is_active')
    search_fields = ('user__email', 'device_identifier', 'name', 'operating_system', 'browser')
    ordering = ('-last_seen_at',)


@admin.register(LoginVerificationChallenge)
class LoginVerificationChallengeAdmin(admin.ModelAdmin):
    """Admin configuration for login verification challenges."""

    list_display = ('id', 'user', 'challenge_id', 'status', 'expires_at', 'attempts')
    list_filter = ('status',)
    search_fields = ('user__email', 'challenge_id', 'device_identifier', 'ip_address')
    ordering = ('-created_at',)


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    """Admin configuration for login attempts."""

    list_display = ('id', 'email', 'ip_address', 'failed_count', 'locked_until', 'last_failed_at')
    list_filter = ('locked_until',)
    search_fields = ('email', 'ip_address', 'last_failure_reason')
    ordering = ('-last_failed_at',)


@admin.register(LoginRateLimit)
class LoginRateLimitAdmin(admin.ModelAdmin):
    """Admin configuration for login rate limits."""

    list_display = ('id', 'scope', 'key', 'action', 'attempt_count', 'blocked_until', 'last_attempt_at')
    list_filter = ('scope', 'action')
    search_fields = ('key',)
    ordering = ('-last_attempt_at',)


@admin.register(IpReputation)
class IpReputationAdmin(admin.ModelAdmin):
    """Admin configuration for IP reputation entries."""

    list_display = ('id', 'ip_address', 'risk_level', 'is_active', 'last_seen_at')
    list_filter = ('risk_level', 'is_active')
    search_fields = ('ip_address', 'reason', 'source')
    ordering = ('-last_seen_at',)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Admin configuration for RBAC roles."""

    list_display = ('id', 'code', 'name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')
    ordering = ('code',)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """Admin configuration for RBAC permissions."""

    list_display = ('id', 'code', 'name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')
    ordering = ('code',)


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    """Admin configuration for role-permission mappings."""

    list_display = ('id', 'role', 'permission', 'created_at')
    list_filter = ('role', 'permission')
    search_fields = ('role__code', 'permission__code')
    ordering = ('-created_at',)


@admin.register(UserRoleAssignment)
class UserRoleAssignmentAdmin(admin.ModelAdmin):
    """Admin configuration for user-role assignments."""

    list_display = ('id', 'user', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active')
    search_fields = ('user__email', 'role__code')
    ordering = ('-created_at',)


@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    """Admin configuration for refresh tokens."""

    list_display = ('id', 'user', 'jti', 'issued_at', 'expires_at', 'revoked_at')
    list_filter = ('revoked_at',)
    search_fields = ('user__email', 'jti')
    ordering = ('-issued_at',)
