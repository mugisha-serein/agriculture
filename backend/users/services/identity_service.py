"""Identity service workflows for registration, activation, and authentication."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone as datetime_timezone
import hashlib
import secrets
import uuid
import urllib.error
import urllib.request

from django.conf import settings
from django.core import signing
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated, Throttled, ValidationError
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken as JwtRefreshToken
from rest_framework_simplejwt.tokens import UntypedToken

from users.models import (
    DeviceType,
    IpReputation,
    IpReputationRisk,
    LoginAttempt,
    LoginChallengeStatus,
    LoginRateLimit,
    LoginVerificationChallenge,
    RateLimitScope,
    RefreshToken,
    User,
    UserDevice,
    UserSession,
)


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
    device: UserDevice | None
    access_token: str
    refresh_token: str
    access_expires_at: datetime
    refresh_expires_at: datetime


@dataclass(frozen=True, slots=True)
class LoginVerificationRequired:
    """Result returned when extra login verification is required."""

    user: User
    challenge_id: uuid.UUID
    expires_at: datetime
    verification_code: str | None


class IdentityService:
    """Application service for the identity domain."""

    activation_salt = 'identity.account.activation'
    activation_max_age_seconds = 60 * 60 * 24
    login_challenge_ttl_minutes = 10
    login_attempt_window_minutes = 15
    login_attempt_max_failures = 5
    login_lockout_minutes = 15
    login_rate_limit_window_seconds = 60
    login_rate_limit_block_seconds = 300
    login_rate_limit_ip_max_attempts = 30
    login_rate_limit_device_max_attempts = 25
    login_rate_limit_user_max_attempts = 20
    login_rate_limit_action_login = 'login'
    login_rate_limit_action_verify = 'login_verify'

    def register_user(self, email, first_name, last_name, phone, password, role):
        """Create an inactive user and issue an activation token."""
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError({'email': ['A user with this email already exists.']})
        self._ensure_password_not_pwned(password)
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

    def login(
        self,
        email,
        password,
        user_agent='',
        ip_address=None,
        device_id=None,
        device_name='',
        device_type=None,
        device_os='',
        device_browser='',
        app_version='',
    ):
        """Authenticate credentials, create session, and issue token pair."""
        normalized_email = self._normalize_email(email)
        self._enforce_login_rate_limits(
            email=normalized_email,
            ip_address=ip_address,
            device_id=device_id,
            user_agent=user_agent,
            action=self.login_rate_limit_action_login,
        )
        self._ensure_login_allowed(email=normalized_email, ip_address=ip_address)
        try:
            user = self._authenticate_credentials(email=normalized_email, password=password)
        except AuthenticationFailed as exc:
            self._record_failed_login(
                email=normalized_email,
                ip_address=ip_address,
                reason=str(exc.detail),
            )
            raise
        user.last_login = timezone.now()
        user.save(update_fields=['last_login', 'updated_at'])
        self._clear_failed_logins(email=normalized_email, ip_address=ip_address, user=user)
        if self._requires_login_verification(
            user=user,
            device_id=device_id,
            ip_address=ip_address,
        ):
            challenge = self._create_login_challenge(
                user=user,
                device_id=device_id,
                device_name=device_name,
                device_type=device_type,
                device_os=device_os,
                device_browser=device_browser,
                app_version=app_version,
                user_agent=user_agent,
                ip_address=ip_address,
            )
            return LoginVerificationRequired(
                user=user,
                challenge_id=challenge.challenge_id,
                expires_at=challenge.expires_at,
                verification_code=challenge.debug_code or None,
            )
        device = self._upsert_device(
            user=user,
            device_id=device_id,
            device_name=device_name,
            device_type=device_type,
            device_os=device_os,
            device_browser=device_browser,
            app_version=app_version,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        session = self._create_session(
            user=user,
            user_agent=user_agent,
            ip_address=ip_address,
            device=device,
        )
        return self._issue_tokens(user=user, session=session)

    def verify_login_challenge(self, challenge_id, verification_code, user_agent='', ip_address=None):
        """Validate a login challenge and issue tokens."""
        challenge = self._validate_login_challenge(
            challenge_id=challenge_id,
            verification_code=verification_code,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        device = self._upsert_device(
            user=challenge.user,
            device_id=challenge.device_identifier,
            device_name=challenge.device_name,
            device_type=challenge.device_type,
            device_os=challenge.operating_system,
            device_browser=challenge.browser,
            app_version=challenge.app_version,
            user_agent=user_agent or challenge.user_agent,
            ip_address=ip_address or challenge.ip_address,
        )
        session = self._create_session(
            user=challenge.user,
            user_agent=user_agent or challenge.user_agent,
            ip_address=ip_address or challenge.ip_address,
            device=device,
        )
        return self._issue_tokens(user=challenge.user, session=session)

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

    def _create_session(self, user, user_agent='', ip_address=None, device=None):
        """Create a new user session based on refresh token lifetime."""
        now = timezone.now()
        return UserSession.objects.create(
            user=user,
            device=device,
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
        if session.device:
            session.device.last_seen_at = timezone.now()
            session.device.save(update_fields=['last_seen_at', 'updated_at'])
        return AuthenticationResult(
            user=user,
            session=session,
            device=session.device,
            access_token=raw_access_token,
            refresh_token=raw_refresh_token,
            access_expires_at=access_expires_at,
            refresh_expires_at=refresh_expires_at,
        )

    def _upsert_device(
        self,
        user,
        device_id=None,
        device_name='',
        device_type=None,
        device_os='',
        device_browser='',
        app_version='',
        user_agent='',
        ip_address=None,
    ):
        """Create or update a tracked device for the user."""
        normalized_id = (device_id or '').strip()
        if not normalized_id:
            normalized_id = str(uuid.uuid4())
        now = timezone.now()
        device, created = UserDevice.objects.get_or_create(
            user=user,
            device_identifier=normalized_id,
            defaults={
                'name': device_name or '',
                'device_type': device_type or DeviceType.OTHER,
                'operating_system': device_os or '',
                'browser': device_browser or '',
                'app_version': app_version or '',
                'user_agent': user_agent or '',
                'last_ip_address': ip_address,
                'first_seen_at': now,
                'last_seen_at': now,
            },
        )
        if not created:
            device.name = device_name or device.name
            device.device_type = device_type or device.device_type
            device.operating_system = device_os or device.operating_system
            device.browser = device_browser or device.browser
            device.app_version = app_version or device.app_version
            device.user_agent = user_agent or device.user_agent
            device.last_ip_address = ip_address or device.last_ip_address
            device.last_seen_at = now
            device.save(
                update_fields=[
                    'name',
                    'device_type',
                    'operating_system',
                    'browser',
                    'app_version',
                    'user_agent',
                    'last_ip_address',
                    'last_seen_at',
                    'updated_at',
                ]
            )
        return device

    def _requires_login_verification(self, user, device_id=None, ip_address=None):
        """Return whether a login requires extra verification."""
        if self._is_ip_high_risk(ip_address):
            return True
        if not UserDevice.objects.filter(user=user).exists():
            return False
        normalized_id = (device_id or '').strip()
        if not normalized_id:
            return True
        try:
            device = UserDevice.objects.get(user=user, device_identifier=normalized_id)
        except UserDevice.DoesNotExist:
            return True
        if ip_address and device.last_ip_address and ip_address != device.last_ip_address:
            return True
        return False

    @staticmethod
    def _is_ip_high_risk(ip_address):
        """Return whether the IP address is marked high risk."""
        if not ip_address:
            return False
        return IpReputation.objects.filter(
            ip_address=ip_address,
            is_active=True,
            risk_level=IpReputationRisk.HIGH,
        ).exists()

    def _create_login_challenge(
        self,
        user,
        device_id=None,
        device_name='',
        device_type=None,
        device_os='',
        device_browser='',
        app_version='',
        user_agent='',
        ip_address=None,
    ):
        """Create a login verification challenge for anomalous activity."""
        raw_code = self._generate_verification_code()
        now = timezone.now()
        expires_at = now + timedelta(minutes=self.login_challenge_ttl_minutes)
        challenge = LoginVerificationChallenge.objects.create(
            user=user,
            device_identifier=(device_id or '').strip(),
            device_name=device_name or '',
            device_type=device_type or DeviceType.OTHER,
            operating_system=device_os or '',
            browser=device_browser or '',
            app_version=app_version or '',
            user_agent=user_agent or '',
            ip_address=ip_address,
            code_hash=self._hash_token(raw_code),
            debug_code=raw_code if settings.DEBUG else '',
            expires_at=expires_at,
        )
        return challenge

    def _validate_login_challenge(self, challenge_id, verification_code, ip_address=None, user_agent=''):
        """Validate a login challenge and return it if successful."""
        try:
            challenge = LoginVerificationChallenge.objects.select_related('user').get(
                challenge_id=challenge_id
            )
        except LoginVerificationChallenge.DoesNotExist as exc:
            raise ValidationError({'challenge_id': ['Login challenge was not found.']}) from exc

        self._enforce_login_rate_limits(
            email=challenge.user.email,
            user_id=challenge.user_id,
            ip_address=ip_address or challenge.ip_address,
            device_id=challenge.device_identifier,
            user_agent=user_agent or challenge.user_agent,
            action=self.login_rate_limit_action_verify,
        )

        if challenge.status != LoginChallengeStatus.PENDING:
            raise ValidationError({'challenge_id': ['Login challenge is not pending.']})

        now = timezone.now()
        if challenge.expires_at <= now:
            challenge.status = LoginChallengeStatus.EXPIRED
            challenge.save(update_fields=['status', 'updated_at'])
            raise ValidationError({'challenge_id': ['Login challenge has expired.']})

        challenge.attempts += 1
        if challenge.attempts > challenge.max_attempts:
            challenge.status = LoginChallengeStatus.FAILED
            challenge.save(update_fields=['attempts', 'status', 'updated_at'])
            raise ValidationError({'verification_code': ['Maximum verification attempts exceeded.']})

        if challenge.code_hash != self._hash_token(verification_code):
            challenge.save(update_fields=['attempts', 'updated_at'])
            raise ValidationError({'verification_code': ['Verification code is invalid.']})

        challenge.status = LoginChallengeStatus.VERIFIED
        challenge.verified_at = now
        challenge.save(update_fields=['attempts', 'status', 'verified_at', 'updated_at'])
        return challenge

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

    def _ensure_login_allowed(self, email, ip_address=None):
        """Raise if the login is currently locked out."""
        attempt = LoginAttempt.objects.filter(email=email, ip_address=ip_address).first()
        if attempt is None:
            return
        now = timezone.now()
        if attempt.locked_until and attempt.locked_until > now:
            raise AuthenticationFailed('Too many failed login attempts. Try again later.')
        if attempt.locked_until and attempt.locked_until <= now:
            attempt.failed_count = 0
            attempt.first_failed_at = None
            attempt.last_failed_at = None
            attempt.locked_until = None
            attempt.save(
                update_fields=[
                    'failed_count',
                    'first_failed_at',
                    'last_failed_at',
                    'locked_until',
                    'updated_at',
                ]
            )
            return
        if attempt.last_failed_at and now - attempt.last_failed_at > timedelta(
            minutes=self.login_attempt_window_minutes
        ):
            attempt.failed_count = 0
            attempt.first_failed_at = None
            attempt.last_failed_at = None
            attempt.locked_until = None
            attempt.save(
                update_fields=[
                    'failed_count',
                    'first_failed_at',
                    'last_failed_at',
                    'locked_until',
                    'updated_at',
                ]
            )

    def _record_failed_login(self, email, ip_address=None, reason=''):
        """Record a failed login attempt for brute-force protection."""
        now = timezone.now()
        user = User.objects.filter(email__iexact=email).first()
        attempt = LoginAttempt.objects.filter(email=email, ip_address=ip_address).first()
        if attempt is None:
            attempt = LoginAttempt.objects.create(
                email=email,
                ip_address=ip_address,
                user=user,
                first_failed_at=now,
                last_failed_at=now,
            )
        if attempt.user is None and user is not None:
            attempt.user = user
        window = timedelta(minutes=self.login_attempt_window_minutes)
        if attempt.first_failed_at and now - attempt.first_failed_at > window:
            attempt.failed_count = 0
            attempt.first_failed_at = now
        if attempt.first_failed_at is None:
            attempt.first_failed_at = now
        attempt.failed_count += 1
        attempt.last_failed_at = now
        attempt.last_failure_reason = (reason or '')[:255]
        if attempt.failed_count >= self.login_attempt_max_failures:
            attempt.locked_until = now + timedelta(minutes=self.login_lockout_minutes)
        attempt.save(
            update_fields=[
                'user',
                'failed_count',
                'first_failed_at',
                'last_failed_at',
                'locked_until',
                'last_failure_reason',
                'updated_at',
            ]
        )

    def _clear_failed_logins(self, email, ip_address=None, user=None):
        """Clear failed login counters after a successful login."""
        LoginAttempt.objects.filter(email=email, ip_address=ip_address).delete()

    @staticmethod
    def _normalize_email(email):
        """Return a normalized email for consistent login tracking."""
        return (email or '').strip().lower()

    def _enforce_login_rate_limits(
        self,
        *,
        email=None,
        user_id=None,
        ip_address=None,
        device_id=None,
        user_agent='',
        action='login',
    ):
        """Apply IP, device, and user rate limits to login endpoints."""
        window_seconds = getattr(
            settings,
            'LOGIN_RATE_LIMIT_WINDOW_SECONDS',
            self.login_rate_limit_window_seconds,
        )
        block_seconds = getattr(
            settings,
            'LOGIN_RATE_LIMIT_BLOCK_SECONDS',
            self.login_rate_limit_block_seconds,
        )
        ip_max = getattr(settings, 'LOGIN_RATE_LIMIT_IP_MAX', self.login_rate_limit_ip_max_attempts)
        device_max = getattr(
            settings,
            'LOGIN_RATE_LIMIT_DEVICE_MAX',
            self.login_rate_limit_device_max_attempts,
        )
        user_max = getattr(settings, 'LOGIN_RATE_LIMIT_USER_MAX', self.login_rate_limit_user_max_attempts)

        self._apply_rate_limit(
            scope=RateLimitScope.IP,
            key=ip_address,
            action=action,
            max_attempts=ip_max,
            window_seconds=window_seconds,
            block_seconds=block_seconds,
        )
        self._apply_rate_limit(
            scope=RateLimitScope.DEVICE,
            key=self._device_rate_key(device_id=device_id, ip_address=ip_address, user_agent=user_agent),
            action=action,
            max_attempts=device_max,
            window_seconds=window_seconds,
            block_seconds=block_seconds,
        )
        self._apply_rate_limit(
            scope=RateLimitScope.USER,
            key=self._user_rate_key(email=email, user_id=user_id),
            action=action,
            max_attempts=user_max,
            window_seconds=window_seconds,
            block_seconds=block_seconds,
        )

    def _apply_rate_limit(
        self,
        *,
        scope,
        key,
        action,
        max_attempts,
        window_seconds,
        block_seconds,
    ):
        """Increment a rate limit counter and raise if limit exceeded."""
        if not key or not max_attempts or max_attempts <= 0:
            return
        now = timezone.now()
        with transaction.atomic():
            record = (
                LoginRateLimit.objects.select_for_update()
                .filter(scope=scope, key=key, action=action)
                .first()
            )
            if record is None:
                record = LoginRateLimit.objects.create(
                    scope=scope,
                    key=key,
                    action=action,
                    window_started_at=now,
                    last_attempt_at=now,
                    attempt_count=1,
                )
            else:
                if record.blocked_until and record.blocked_until > now:
                    wait_seconds = int((record.blocked_until - now).total_seconds())
                    raise Throttled(
                        wait=wait_seconds,
                        detail=self._rate_limit_detail(scope=scope, action=action),
                    )
                if record.window_started_at and now - record.window_started_at > timedelta(
                    seconds=window_seconds
                ):
                    record.window_started_at = now
                    record.attempt_count = 0
                    record.blocked_until = None
                record.attempt_count += 1
                record.last_attempt_at = now
                if record.attempt_count > max_attempts:
                    record.blocked_until = now + timedelta(seconds=block_seconds)
                    record.save(
                        update_fields=[
                            'window_started_at',
                            'last_attempt_at',
                            'attempt_count',
                            'blocked_until',
                            'updated_at',
                        ]
                    )
                    wait_seconds = int((record.blocked_until - now).total_seconds())
                    raise Throttled(
                        wait=wait_seconds,
                        detail=self._rate_limit_detail(scope=scope, action=action),
                    )
                record.save(
                    update_fields=[
                        'window_started_at',
                        'last_attempt_at',
                        'attempt_count',
                        'blocked_until',
                        'updated_at',
                    ]
                )

    @staticmethod
    def _device_rate_key(*, device_id=None, ip_address=None, user_agent=''):
        """Return a stable key for device rate limiting."""
        normalized = (device_id or '').strip()
        if normalized:
            return normalized
        raw = f'{ip_address or ""}|{user_agent or ""}'.strip()
        if not raw:
            return None
        return f'anon:{IdentityService._hash_token(raw)}'

    @staticmethod
    def _user_rate_key(*, email=None, user_id=None):
        """Return a stable key for user rate limiting."""
        if user_id:
            return f'id:{user_id}'
        normalized_email = IdentityService._normalize_email(email or '')
        return normalized_email or None

    def _rate_limit_detail(self, *, scope, action):
        """Return a human-readable rate limit error message."""
        endpoint = 'login verification' if action == self.login_rate_limit_action_verify else 'login'
        if scope == RateLimitScope.IP:
            subject = 'IP'
        elif scope == RateLimitScope.DEVICE:
            subject = 'device'
        else:
            subject = 'user'
        return f'Too many {endpoint} attempts for this {subject}. Try again later.'

    @staticmethod
    def _hash_token(raw_token):
        """Return a deterministic hash for sensitive token storage."""
        return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()

    @staticmethod
    def _generate_verification_code():
        """Return a numeric verification code for login challenges."""
        return ''.join(secrets.choice('0123456789') for _ in range(6))

    def _ensure_password_not_pwned(self, password):
        """Reject passwords that appear in known breach corpuses."""
        if not getattr(settings, 'HIBP_ENABLED', False):
            return
        count = self._pwned_password_count(password)
        if count is None:
            if getattr(settings, 'HIBP_FAIL_CLOSED', True):
                raise ValidationError(
                    {'password': ['Unable to validate password safety. Please try again.']}
                )
            return
        if count >= getattr(settings, 'HIBP_MIN_BREACH_COUNT', 1):
            raise ValidationError(
                {'password': ['This password has appeared in data breaches. Choose a different password.']}
            )

    def _pwned_password_count(self, password):
        """Return the breach count for a password using the HIBP range API."""
        if not password:
            return 0
        sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
        prefix = sha1_hash[:5]
        suffix = sha1_hash[5:]
        base_url = getattr(settings, 'HIBP_API_URL', 'https://api.pwnedpasswords.com/range/')
        url = f"{base_url.rstrip('/')}/{prefix}"
        headers = {
            'User-Agent': getattr(settings, 'HIBP_USER_AGENT', 'AgricultureBackend/1.0'),
            'Add-Padding': 'true',
        }
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(
                request,
                timeout=getattr(settings, 'HIBP_TIMEOUT_SECONDS', 4),
            ) as response:
                body = response.read().decode('utf-8')
        except urllib.error.URLError:
            return None
        for line in body.splitlines():
            if not line:
                continue
            parts = line.split(':', 1)
            if len(parts) != 2:
                continue
            if parts[0].strip().upper() == suffix:
                try:
                    return int(parts[1].strip())
                except ValueError:
                    return 0
        return 0
