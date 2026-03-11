"""Identity app API tests."""

from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import (
    IpReputation,
    IpReputationRisk,
    LoginVerificationChallenge,
    Role,
    User,
    UserDevice,
    UserRoleAssignment,
    UserSession,
)


class IdentityApiTests(APITestCase):
    """End-to-end tests for identity app API flows."""

    def test_registration_creates_inactive_user(self):
        """Registration should create an inactive user with activation token."""
        response = self.client.post(
            reverse('identity:register'),
            {
                'email': 'seller@example.com',
                'first_name': 'Seller',
                'last_name': 'One',
                'phone': '1234567890',
                'password': 'StrongPass123',
                'role': 'seller',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('activation_token', response.data)
        user = User.objects.get(email='seller@example.com')
        self.assertFalse(user.is_active)
        self.assertEqual(user.role, 'seller')

    def test_activation_login_and_verification_flow(self):
        """User can activate account, log in, and verify access token."""
        registration = self.client.post(
            reverse('identity:register'),
            {
                'email': 'buyer@example.com',
                'first_name': 'Buyer',
                'last_name': 'One',
                'phone': '1234567890',
                'password': 'StrongPass123',
                'role': 'buyer',
            },
            format='json',
        )

        blocked_login = self.client.post(
            reverse('identity:login'),
            {'email': 'buyer@example.com', 'password': 'StrongPass123'},
            format='json',
        )
        self.assertEqual(blocked_login.status_code, status.HTTP_401_UNAUTHORIZED)

        activation = self.client.post(
            reverse('identity:activate'),
            {'token': registration.data['activation_token']},
            format='json',
        )
        self.assertEqual(activation.status_code, status.HTTP_200_OK)

        login = self.client.post(
            reverse('identity:login'),
            {'email': 'buyer@example.com', 'password': 'StrongPass123'},
            format='json',
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', login.data)

        verify = self.client.post(
            reverse('identity:verify'),
            {'access_token': login.data['access_token']},
            format='json',
        )
        self.assertEqual(verify.status_code, status.HTTP_200_OK)
        self.assertTrue(verify.data['is_valid'])

    def test_refresh_rotation_and_logout(self):
        """Refresh rotates tokens and logout revokes the latest token."""
        registration = self.client.post(
            reverse('identity:register'),
            {
                'email': 'transporter@example.com',
                'first_name': 'Transporter',
                'last_name': 'One',
                'phone': '1234567890',
                'password': 'StrongPass123',
                'role': 'transporter',
            },
            format='json',
        )
        self.client.post(
            reverse('identity:activate'),
            {'token': registration.data['activation_token']},
            format='json',
        )
        User.objects.filter(email='transporter@example.com').update(is_verified=True)
        login = self.client.post(
            reverse('identity:login'),
            {'email': 'transporter@example.com', 'password': 'StrongPass123'},
            format='json',
        )

        old_refresh = login.data['refresh_token']
        rotated = self.client.post(
            reverse('identity:refresh'),
            {'refresh_token': old_refresh},
            format='json',
        )
        self.assertEqual(rotated.status_code, status.HTTP_200_OK)
        self.assertNotEqual(old_refresh, rotated.data['refresh_token'])

        reused = self.client.post(
            reverse('identity:refresh'),
            {'refresh_token': old_refresh},
            format='json',
        )
        self.assertEqual(reused.status_code, status.HTTP_401_UNAUTHORIZED)

        logout = self.client.post(
            reverse('identity:logout'),
            {'refresh_token': rotated.data['refresh_token']},
            format='json',
        )
        self.assertEqual(logout.status_code, status.HTTP_200_OK)

        revoked = self.client.post(
            reverse('identity:refresh'),
            {'refresh_token': rotated.data['refresh_token']},
            format='json',
        )
        self.assertEqual(revoked.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_tracks_device_metadata(self):
        """Login should create and associate a tracked device."""
        registration = self.client.post(
            reverse('identity:register'),
            {
                'email': 'device@example.com',
                'first_name': 'Device',
                'last_name': 'User',
                'phone': '1234567890',
                'password': 'StrongPass123',
                'role': 'buyer',
            },
            format='json',
        )
        self.client.post(
            reverse('identity:activate'),
            {'token': registration.data['activation_token']},
            format='json',
        )

        login = self.client.post(
            reverse('identity:login'),
            {
                'email': 'device@example.com',
                'password': 'StrongPass123',
                'user_agent': 'Mozilla/5.0',
                'device_id': 'device-123',
                'device_name': 'Pixel 7',
                'device_type': 'mobile',
                'device_os': 'Android',
                'device_browser': 'Chrome',
                'app_version': '1.0.0',
            },
            format='json',
        )

        self.assertEqual(login.status_code, status.HTTP_200_OK)
        device = UserDevice.objects.get(user__email='device@example.com', device_identifier='device-123')
        self.assertEqual(device.device_type, 'mobile')
        self.assertEqual(device.operating_system, 'Android')
        self.assertEqual(device.browser, 'Chrome')
        self.assertEqual(device.app_version, '1.0.0')
        session = UserSession.objects.get(id=login.data['session_id'])
        self.assertEqual(session.device_id, device.id)

    @override_settings(DEBUG=True)
    def test_login_requires_verification_for_new_device(self):
        """Anomalous logins should require extra verification."""
        registration = self.client.post(
            reverse('identity:register'),
            {
                'email': 'anomaly@example.com',
                'first_name': 'Anomaly',
                'last_name': 'User',
                'phone': '1234567890',
                'password': 'StrongPass123',
                'role': 'buyer',
            },
            format='json',
        )
        self.client.post(
            reverse('identity:activate'),
            {'token': registration.data['activation_token']},
            format='json',
        )

        first_login = self.client.post(
            reverse('identity:login'),
            {
                'email': 'anomaly@example.com',
                'password': 'StrongPass123',
                'device_id': 'device-1',
            },
            format='json',
        )
        self.assertEqual(first_login.status_code, status.HTTP_200_OK)

        second_login = self.client.post(
            reverse('identity:login'),
            {
                'email': 'anomaly@example.com',
                'password': 'StrongPass123',
                'device_id': 'device-2',
            },
            format='json',
        )
        self.assertEqual(second_login.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(second_login.data['verification_required'])

        challenge = LoginVerificationChallenge.objects.get(
            challenge_id=second_login.data['challenge_id']
        )
        verify = self.client.post(
            reverse('identity:login-verify'),
            {
                'challenge_id': str(challenge.challenge_id),
                'verification_code': second_login.data['verification_code'],
            },
            format='json',
        )
        self.assertEqual(verify.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', verify.data)

    @override_settings(DEBUG=True)
    def test_login_requires_verification_for_high_risk_ip(self):
        """High-risk IPs should require extra verification."""
        registration = self.client.post(
            reverse('identity:register'),
            {
                'email': 'iprisk@example.com',
                'first_name': 'IP',
                'last_name': 'Risk',
                'phone': '1234567890',
                'password': 'StrongPass123',
                'role': 'buyer',
            },
            format='json',
        )
        self.client.post(
            reverse('identity:activate'),
            {'token': registration.data['activation_token']},
            format='json',
        )

        IpReputation.objects.create(
            ip_address='10.0.0.1',
            risk_level=IpReputationRisk.HIGH,
            source='test',
            reason='known bad',
        )

        login = self.client.post(
            reverse('identity:login'),
            {
                'email': 'iprisk@example.com',
                'password': 'StrongPass123',
                'device_id': 'device-risk',
            },
            format='json',
            HTTP_X_FORWARDED_FOR='10.0.0.1',
        )
        self.assertEqual(login.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(login.data['verification_required'])

        verify = self.client.post(
            reverse('identity:login-verify'),
            {
                'challenge_id': login.data['challenge_id'],
                'verification_code': login.data['verification_code'],
            },
            format='json',
            HTTP_X_FORWARDED_FOR='10.0.0.1',
        )
        self.assertEqual(verify.status_code, status.HTTP_200_OK)

    def test_login_bruteforce_lockout(self):
        """Repeated failed logins should trigger a lockout."""
        registration = self.client.post(
            reverse('identity:register'),
            {
                'email': 'lockout@example.com',
                'first_name': 'Lock',
                'last_name': 'Out',
                'phone': '1234567890',
                'password': 'StrongPass123',
                'role': 'buyer',
            },
            format='json',
        )
        self.client.post(
            reverse('identity:activate'),
            {'token': registration.data['activation_token']},
            format='json',
        )

        for _ in range(5):
            failed = self.client.post(
                reverse('identity:login'),
                {'email': 'lockout@example.com', 'password': 'WrongPass123'},
                format='json',
            )
            self.assertEqual(failed.status_code, status.HTTP_401_UNAUTHORIZED)

        locked = self.client.post(
            reverse('identity:login'),
            {'email': 'lockout@example.com', 'password': 'StrongPass123'},
            format='json',
        )
        self.assertEqual(locked.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('Too many failed login attempts', locked.data['detail'])

    def test_role_system_seeds_and_assignments(self):
        """RBAC roles are seeded and can be assigned to users."""
        seeded = set(Role.objects.values_list('code', flat=True))
        for code in ['admin', 'buyer', 'seller', 'transporter']:
            self.assertIn(code, seeded)
        buyer_role = Role.objects.get(code='buyer')
        user = User.objects.create_user(
            email='rbac@example.com',
            first_name='RBAC',
            last_name='User',
            phone='1234567890',
            password='StrongPass123',
            role='buyer',
            is_active=True,
        )
        user.roles.add(buyer_role)
        self.assertTrue(user.roles.filter(code='buyer').exists())
        assignment = UserRoleAssignment.objects.get(user=user, role=buyer_role)
        self.assertTrue(assignment.is_active)

    @override_settings(
        LOGIN_RATE_LIMIT_WINDOW_SECONDS=60,
        LOGIN_RATE_LIMIT_BLOCK_SECONDS=300,
        LOGIN_RATE_LIMIT_IP_MAX=2,
        LOGIN_RATE_LIMIT_DEVICE_MAX=2,
        LOGIN_RATE_LIMIT_USER_MAX=2,
    )
    def test_login_rate_limiting_blocks_after_threshold(self):
        """Login rate limiting should throttle after the configured threshold."""
        registration = self.client.post(
            reverse('identity:register'),
            {
                'email': 'ratelimit@example.com',
                'first_name': 'Rate',
                'last_name': 'Limit',
                'phone': '1234567890',
                'password': 'StrongPass123',
                'role': 'buyer',
            },
            format='json',
        )
        self.client.post(
            reverse('identity:activate'),
            {'token': registration.data['activation_token']},
            format='json',
        )

        payload = {
            'email': 'ratelimit@example.com',
            'password': 'StrongPass123',
            'device_id': 'rate-limit-device',
        }
        first = self.client.post(reverse('identity:login'), payload, format='json')
        second = self.client.post(reverse('identity:login'), payload, format='json')
        third = self.client.post(reverse('identity:login'), payload, format='json')

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(third.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('detail', third.data)

    @override_settings(HIBP_ENABLED=True, HIBP_FAIL_CLOSED=True)
    def test_registration_rejects_breached_password(self):
        """Registration should reject a password found in breaches."""
        with patch(
            'users.services.identity_service.IdentityService._pwned_password_count',
            return_value=5,
        ):
            response = self.client.post(
                reverse('identity:register'),
                {
                    'email': 'breached@example.com',
                    'first_name': 'Breach',
                    'last_name': 'User',
                    'phone': '1234567890',
                    'password': 'Password123!',
                    'role': 'buyer',
                },
                format='json',
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
