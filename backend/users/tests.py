"""Identity app API tests."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User


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
