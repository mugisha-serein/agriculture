"""Admin registrations for identity models."""

from django.contrib import admin

from users.models import RefreshToken, User, UserSession


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Admin configuration for users."""

    list_display = ('id', 'email', 'first_name', 'last_name', 'phone', 'role', 'is_active', 'is_staff', 'created_at')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('-created_at',)


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """Admin configuration for sessions."""

    list_display = ('id', 'user', 'ip_address', 'started_at', 'expires_at', 'revoked_at')
    list_filter = ('revoked_at',)
    search_fields = ('user__email', 'ip_address', 'user_agent')
    ordering = ('-started_at',)


@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    """Admin configuration for refresh tokens."""

    list_display = ('id', 'user', 'jti', 'issued_at', 'expires_at', 'revoked_at')
    list_filter = ('revoked_at',)
    search_fields = ('user__email', 'jti')
    ordering = ('-issued_at',)
