"""Verification app API tests."""

import shutil
import tempfile
from pathlib import Path

from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from users.models import User
from verification.models import UserVerification


class VerificationApiTests(APITestCase):
    """End-to-end verification API behavior tests."""

    @classmethod
    def setUpClass(cls):
        """Create an isolated media directory for upload tests."""
        super().setUpClass()
        tmp_root = Path(settings.BASE_DIR) / 'tmp'
        tmp_root.mkdir(parents=True, exist_ok=True)
        cls._media_root = tempfile.mkdtemp(prefix='verification-tests-', dir=tmp_root)
        cls._override = override_settings(MEDIA_ROOT=cls._media_root)
        cls._override.enable()

    @classmethod
    def tearDownClass(cls):
        """Remove temporary media storage after tests complete."""
        cls._override.disable()
        shutil.rmtree(cls._media_root, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        """Create user fixtures for verification flow tests."""
        self.user = User.objects.create_user(
            email='buyer@example.com',
            first_name='Buyer',
            last_name='One',
            password='StrongPass123',
            role='buyer',
            is_active=True,
        )
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            first_name='Buyer',
            last_name='One',
            password='StrongPass123',
            role='admin',
            is_active=True,
            is_staff=True,
        )

    def _front_file(self, suffix='1'):
        """Create an in-memory front document upload."""
        return SimpleUploadedFile(
            name=f'front_{suffix}.jpg',
            content=b'front-image-bytes',
            content_type='image/jpeg',
        )

    def _back_file(self, suffix='1'):
        """Create an in-memory back document upload."""
        return SimpleUploadedFile(
            name=f'back_{suffix}.jpg',
            content=b'back-image-bytes',
            content_type='image/jpeg',
        )

    def test_user_can_submit_verification(self):
        """Authenticated user can submit verification documents."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse('verification:submit'),
            data={
                'document_type': 'national_id',
                'document_number': 'ID-123456',
                'document_front': self._front_file('a'),
                'document_back': self._back_file('a'),
            },
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'pending')
        verification = UserVerification.objects.get(user=self.user, is_current=True)
        self.assertTrue(verification.documents.exists())
        self.assertEqual(len(response.data['documents']), 1)

    def test_resubmission_retires_previous_current_record(self):
        """Submitting again should retire old current verification record."""
        self.client.force_authenticate(user=self.user)
        first = self.client.post(
            reverse('verification:submit'),
            data={
                'document_type': 'passport',
                'document_number': 'P-11111',
                'document_front': self._front_file('first'),
                'expiry_date': '2030-01-01',
            },
            format='multipart',
        )
        second = self.client.post(
            reverse('verification:submit'),
            data={
                'document_type': 'passport',
                'document_number': 'P-22222',
                'document_front': self._front_file('second'),
                'expiry_date': '2030-02-01',
            },
            format='multipart',
        )

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        current_count = UserVerification.objects.filter(user=self.user, is_current=True).count()
        total_count = UserVerification.objects.filter(user=self.user).count()
        self.assertEqual(current_count, 1)
        self.assertEqual(total_count, 2)

    def test_admin_can_list_pending_and_review(self):
        """Verification admin can list pending submissions and approve them."""
        self.client.force_authenticate(user=self.user)
        submit = self.client.post(
            reverse('verification:submit'),
            data={
                'document_type': 'driver_license',
                'document_number': 'DL-9000',
                'document_front': self._front_file('review'),
                'document_back': self._back_file('review'),
                'expiry_date': '2029-12-31',
            },
            format='multipart',
        )
        verification_id = submit.data['id']

        self.client.force_authenticate(user=self.admin_user)
        pending = self.client.get(reverse('verification:admin-pending'))
        self.assertEqual(pending.status_code, status.HTTP_200_OK)
        self.assertEqual(len(pending.data), 1)

        review = self.client.post(
            reverse('verification:admin-review', kwargs={'verification_id': verification_id}),
            data={
                'status': 'approved',
                'review_notes': 'Documents validated',
            },
            format='json',
        )

        self.assertEqual(review.status_code, status.HTTP_200_OK, review.data)
        self.assertEqual(review.data['status'], 'approved')
        self.assertTrue(review.data['reviews'])
        self.assertTrue(review.data['status_logs'])

    def test_non_admin_cannot_access_admin_endpoints(self):
        """Non-admin users should be blocked from admin verification endpoints."""
        self.client.force_authenticate(user=self.user)
        pending = self.client.get(reverse('verification:admin-pending'))
        self.assertEqual(pending.status_code, status.HTTP_403_FORBIDDEN)
