"""Identity service workflows for registration, activation, and authentication."""

from dataclasses import dataclass
from datetime import datetime, timezone as datetime_timezone
import hashlib
import uuid

from django.conf import settings
from django.core import signing
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated, ValidationError
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken as JwtRefreshToken
from rest_framework_simplejwt.tokens import UntypedToken

from users.models import RefreshToken, User, UserSession


@dataclass(frozen=True, slots=True)
class RegistrationResult:
    """Result returned from user registration."""

    user: User
    activation_token: str


@dataclass(frozen=True, slots=True)
class AuthenticationResult:
    """Result returned from authentication and token issuance."""

    user: User
    session: UserSession
    access_token: str
    refresh_token: str
    access_expires_at: datetime
    refresh_expires_at: datetime


class IdentityService:
    """Application service for the identity domain."""

    activation_salt = 'identity.account.activation'
    activation_max_age_seconds = 60 * 60 * 24

    def register_user(self, email, first_name, last_name, phone, password, role):
        """Create an inactive user and issue an activation token."""
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError({'email': ['A user with this email already exists.']})
        user = User.objects.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            password=password,
            role=role,
        )
        activation_token = signing.dumps(
            {'user_id': user.id, 'email': user.email},
            salt=self.activation_salt,
        )
        return RegistrationResult(user=user, activation_token=activation_token)

    def activate_account(self, token):
        """Activate a user account if the activation token is valid."""
        try:
            payload = signing.loads(
                token,
                salt=self.activation_salt,
                max_age=self.activation_max_age_seconds,
            )
        except signing.BadSignature as exc:
            raise ValidationError({'token': ['Activation token is invalid or expired.']}) from exc

        try:
            user = User.objects.get(id=payload['user_id'], email=payload['email'])
        except User.DoesNotExist as exc:
            raise ValidationError({'token': ['Activation target user was not found.']}) from exc

        if not user.is_active:
            user.is_active = True
            user.activated_at = timezone.now()
            user.save(update_fields=['is_active', 'activated_at', 'updated_at'])
        return user

    def get_user_from_activation_token(self, token):
        """Resolve a user from an activation token without activating them."""
        try:
            payload = signing.loads(
                token,
                salt=self.activation_salt,
                max_age=self.activation_max_age_seconds,
            )
        except signing.BadSignature as exc:
            raise ValidationError({'token': ['Activation token is invalid or expired.']}) from exc

        try:
            return User.objects.get(id=payload['user_id'], email=payload['email'])
        except User.DoesNotExist as exc:
            raise ValidationError({'token': ['Activation target user was not found.']}) from exc

    def login(self, email, password, user_agent='', ip_address=None):
        """Authenticate credentials, create session, and issue token pair."""
        user = self._authenticate_credentials(email=email, password=password)
        user.last_login = timezone.now()
        user.save(update_fields=['last_login', 'updated_at'])
        session = self._create_session(user=user, user_agent=user_agent, ip_address=ip_address)
        return self._issue_tokens(user=user, session=session)

    @transaction.atomic
    def refresh(self, refresh_token):
        """Rotate a refresh token and issue a new token pair."""
        record = self._validate_refresh_record(refresh_token=refresh_token)
        user = record.user
        if not user.is_active:
            raise NotAuthenticated('Account is not activated.')
        result = self._issue_tokens(user=user, session=record.session)
        record.revoked_at = timezone.now()
        record.save(update_fields=['revoked_at', 'updated_at'])
        return result

    @transaction.atomic
    def logout(self, refresh_token):
        """Revoke refresh token and active session."""
        record = self._validate_refresh_record(refresh_token=refresh_token)
        now = timezone.now()
        if record.revoked_at is None:
            record.revoked_at = now
            record.save(update_fields=['revoked_at', 'updated_at'])
        if record.session.revoked_at is None:
            record.session.revoked_at = now
            record.session.save(update_fields=['revoked_at', 'updated_at'])

    def validate_access_token(self, access_token):
        """Validate an access token and return payload fields."""
        try:
            token = UntypedToken(access_token)
        except TokenError as exc:
            raise ValidationError({'access_token': ['Access token is invalid or expired.']}) from exc
        return dict(token.payload)

    def _authenticate_credentials(self, email, password):
        """Validate user credentials against persisted identity data."""
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist as exc:
            raise AuthenticationFailed('Invalid credentials.') from exc
        
        # Admin users are not allowed to access the website
        from users.domain.roles import UserRole
        if user.role == UserRole.ADMIN:
            raise AuthenticationFailed('Administrative access is restricted to the internal dashboard.')

        # Sellers and transporters strictly require verification before login
        if user.role in [UserRole.SELLER, UserRole.TRANSPORTER] and not user.is_verified:
            raise AuthenticationFailed('Your account must be verified by an administrator before you can sign in.')

        if not user.check_password(password):
            raise AuthenticationFailed('Invalid credentials.')
        if not user.is_active:
            raise NotAuthenticated('Account is not activated.')
        return user

    def _create_session(self, user, user_agent='', ip_address=None):
        """Create a new user session based on refresh token lifetime."""
        now = timezone.now()
        return UserSession.objects.create(
            user=user,
            user_agent=user_agent or '',
            ip_address=ip_address,
            started_at=now,
            last_seen_at=now,
            expires_at=now + settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
        )

    def _issue_tokens(self, user, session):
        """Issue JWT tokens and persist refresh token metadata."""
        jwt_refresh = JwtRefreshToken.for_user(user)
        raw_refresh_token = str(jwt_refresh)
        raw_access_token = str(jwt_refresh.access_token)
        refresh_expires_at = datetime.fromtimestamp(
            jwt_refresh['exp'],
            tz=datetime_timezone.utc,
        )
        access_expires_at = datetime.fromtimestamp(
            jwt_refresh.access_token['exp'],
            tz=datetime_timezone.utc,
        )
        RefreshToken.objects.create(
            user=user,
            session=session,
            jti=uuid.UUID(str(jwt_refresh['jti'])),
            token_hash=self._hash_token(raw_refresh_token),
            issued_at=timezone.now(),
            expires_at=refresh_expires_at,
        )
        session.last_seen_at = timezone.now()
        session.save(update_fields=['last_seen_at', 'updated_at'])
        return AuthenticationResult(
            user=user,
            session=session,
            access_token=raw_access_token,
            refresh_token=raw_refresh_token,
            access_expires_at=access_expires_at,
            refresh_expires_at=refresh_expires_at,
        )

    def _validate_refresh_record(self, refresh_token):
        """Validate and return a stored refresh token record."""
        try:
            jwt_refresh = JwtRefreshToken(refresh_token)
        except TokenError as exc:
            raise AuthenticationFailed('Refresh token is invalid or expired.') from exc

        jti = uuid.UUID(str(jwt_refresh['jti']))
        try:
            record = RefreshToken.objects.select_related('session', 'user').get(jti=jti)
        except RefreshToken.DoesNotExist as exc:
            raise AuthenticationFailed('Refresh token is not recognized.') from exc

        if record.token_hash != self._hash_token(refresh_token):
            raise AuthenticationFailed('Refresh token signature mismatch.')
        if record.revoked_at is not None:
            raise AuthenticationFailed('Refresh token has been revoked.')
        if record.expires_at <= timezone.now():
            raise AuthenticationFailed('Refresh token is expired.')
        if record.session.revoked_at is not None:
            raise AuthenticationFailed('Session is revoked.')
        if record.session.expires_at <= timezone.now():
            raise AuthenticationFailed('Session is expired.')
        return record

    @staticmethod
    def _hash_token(raw_token):
        """Return a deterministic hash for sensitive token storage."""
        return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
