"""Payments app API tests."""

from datetime import timedelta

from django.core.exceptions import ValidationError as DjangoValidationError
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from listings.domain.statuses import ListingStatus
from listings.models import Crop, Product, ProductInventory, ProductPricing
from orders.models import Order
from orders.models import OrderItem
from payments.domain.statuses import PaymentStatus
from payments.models import EscrowTransaction
from users.models import User


class PaymentsApiTests(APITestCase):
    """End-to-end tests for payment and escrow workflows."""

    def setUp(self):
        """Create order and listing fixtures used by payment tests."""
        self.buyer = User.objects.create_user(
            email='buyer@example.com',
            full_name='Buyer One',
            password='StrongPass123',
            role='buyer',
            is_active=True,
        )
        self.other_buyer = User.objects.create_user(
            email='buyer2@example.com',
            full_name='Buyer Two',
            password='StrongPass123',
            role='buyer',
            is_active=True,
        )
        self.seller = User.objects.create_user(
            email='seller@example.com',
            full_name='Seller One',
            password='StrongPass123',
            role='seller',
            is_active=True,
        )
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            full_name='Admin One',
            password='StrongPass123',
            role='admin',
            is_active=True,
            is_staff=True,
        )
        self.crop = Crop.objects.create(name='Potato', slug='potato')
        self.product = Product.objects.create(
            seller=self.seller,
            crop=self.crop,
            title='Fresh Potato',
            unit='kg',
            minimum_order_quantity='2.000',
            location_name='Johannesburg',
            expires_at=timezone.now() + timedelta(days=7),
            status=ListingStatus.ACTIVE,
        )
        ProductInventory.objects.create(
            product=self.product,
            available_quantity='100.000',
            reserved_quantity='0.000',
        )
        ProductPricing.objects.create(
            product=self.product,
            currency='USD',
            price='20.00',
            discount='0.00',
            valid_from=timezone.now() - timedelta(days=1),
        )
        self.order = Order.objects.create(
            order_number='ORD-TEST-0001',
            buyer=self.buyer,
            status='pending',
            currency='ZAR',
            subtotal_amount='100.00',
            seller_count=1,
            item_count=1,
            placed_at=timezone.now(),
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            seller=self.seller,
            product_title=self.product.title,
            unit=self.product.unit,
            unit_price='20.00',
            quantity='5.000',
            line_total='100.00',
            status='allocated',
            allocated_at=timezone.now(),
        )

    def _initiate_payment(self, idempotency_key='idem-001'):
        """Initiate payment for test order and return API response."""
        self.client.force_authenticate(user=self.buyer)
        response = self.client.post(
            reverse('payments:initiate'),
            data={
                'order_id': self.order.id,
                'idempotency_key': idempotency_key,
                'provider': 'mock_gateway',
                'amount': '100.00',
                'currency': 'ZAR',
            },
            format='json',
        )
        return response

    def test_initiate_payment_is_idempotent(self):
        """Payment initiation should be idempotent for same request fingerprint."""
        first = self._initiate_payment(idempotency_key='idem-abc')
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(first.data['status'], PaymentStatus.INITIATED)

        second = self._initiate_payment(idempotency_key='idem-abc')
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(first.data['id'], second.data['id'])

    def test_idempotency_key_payload_mismatch_fails(self):
        """Reusing idempotency key with different payload should fail."""
        self._initiate_payment(idempotency_key='idem-mismatch')
        self.client.force_authenticate(user=self.buyer)
        response = self.client.post(
            reverse('payments:initiate'),
            data={
                'order_id': self.order.id,
                'idempotency_key': 'idem-mismatch',
                'provider': 'mock_gateway',
                'amount': '99.99',
                'currency': 'ZAR',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_webhook_capture_creates_escrow_hold_once(self):
        """Capture webhook should create one immutable hold transaction."""
        payment_response = self._initiate_payment(idempotency_key='idem-capture')
        payment_reference = payment_response.data['payment_reference']

        first_webhook = self.client.post(
            reverse('payments:webhook'),
            data={
                'event_id': 'evt-capture-1',
                'event_type': 'payment.captured',
                'payment_reference': payment_reference,
                'amount': '100.00',
                'currency': 'ZAR',
            },
            format='json',
        )
        self.assertEqual(first_webhook.status_code, status.HTTP_200_OK)
        self.assertTrue(first_webhook.data['processed'])
        self.assertEqual(first_webhook.data['payment']['status'], PaymentStatus.ESCROW_HELD)

        duplicate_webhook = self.client.post(
            reverse('payments:webhook'),
            data={
                'event_id': 'evt-capture-1',
                'event_type': 'payment.captured',
                'payment_reference': payment_reference,
                'amount': '100.00',
                'currency': 'ZAR',
            },
            format='json',
        )
        self.assertEqual(duplicate_webhook.status_code, status.HTTP_200_OK)
        self.assertFalse(duplicate_webhook.data['processed'])
        self.assertEqual(EscrowTransaction.objects.filter(payment__payment_reference=payment_reference).count(), 1)

        escrow_transaction = EscrowTransaction.objects.get(payment__payment_reference=payment_reference)
        escrow_transaction.amount = '1.00'
        with self.assertRaises(DjangoValidationError):
            escrow_transaction.save()

    def test_release_and_refund_rules(self):
        """Admin can release held escrow and buyer can refund held escrow only."""
        payment_response = self._initiate_payment(idempotency_key='idem-release')
        payment_id = payment_response.data['id']
        payment_reference = payment_response.data['payment_reference']

        self.client.post(
            reverse('payments:webhook'),
            data={
                'event_id': 'evt-capture-2',
                'event_type': 'payment.captured',
                'payment_reference': payment_reference,
                'amount': '100.00',
                'currency': 'ZAR',
            },
            format='json',
        )

        self.client.force_authenticate(user=self.admin_user)
        release = self.client.post(
            reverse('payments:release', kwargs={'payment_id': payment_id}),
            data={'metadata': {'note': 'Settlement complete'}},
            format='json',
        )
        self.assertEqual(release.status_code, status.HTTP_200_OK)
        self.assertEqual(release.data['status'], PaymentStatus.RELEASED)

        self.client.force_authenticate(user=self.buyer)
        refund_after_release = self.client.post(
            reverse('payments:refund', kwargs={'payment_id': payment_id}),
            data={'reason': 'Late shipment'},
            format='json',
        )
        self.assertEqual(refund_after_release.status_code, status.HTTP_400_BAD_REQUEST)

        second_order = Order.objects.create(
            order_number='ORD-TEST-0002',
            buyer=self.buyer,
            status='pending',
            currency='ZAR',
            subtotal_amount='100.00',
            seller_count=1,
            item_count=1,
            placed_at=timezone.now(),
        )
        OrderItem.objects.create(
            order=second_order,
            product=self.product,
            seller=self.seller,
            product_title=self.product.title,
            unit=self.product.unit,
            unit_price='20.00',
            quantity='5.000',
            line_total='100.00',
            status='allocated',
            allocated_at=timezone.now(),
        )

        second_initiation = self.client.post(
            reverse('payments:initiate'),
            data={
                'order_id': second_order.id,
                'idempotency_key': 'idem-refund-only',
                'provider': 'mock_gateway',
                'amount': '100.00',
                'currency': 'ZAR',
            },
            format='json',
        )
        second_payment_id = second_initiation.data['id']
        second_reference = second_initiation.data['payment_reference']

        self.client.post(
            reverse('payments:webhook'),
            data={
                'event_id': 'evt-capture-3',
                'event_type': 'payment.captured',
                'payment_reference': second_reference,
                'amount': '100.00',
                'currency': 'ZAR',
            },
            format='json',
        )

        refund = self.client.post(
            reverse('payments:refund', kwargs={'payment_id': second_payment_id}),
            data={'reason': 'Order cancelled'},
            format='json',
        )
        self.assertEqual(refund.status_code, status.HTTP_200_OK)
        self.assertEqual(refund.data['status'], PaymentStatus.REFUNDED)

    def test_payment_access_controls(self):
        """Only payment owner buyer or admin can access payment details."""
        payment_response = self._initiate_payment(idempotency_key='idem-access')
        payment_id = payment_response.data['id']

        self.client.force_authenticate(user=self.other_buyer)
        forbidden = self.client.get(reverse('payments:detail', kwargs={'payment_id': payment_id}))
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin_user)
        allowed = self.client.get(reverse('payments:detail', kwargs={'payment_id': payment_id}))
        self.assertEqual(allowed.status_code, status.HTTP_200_OK)
