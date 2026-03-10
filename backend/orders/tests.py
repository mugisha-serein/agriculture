"""Orders app API tests."""

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from listings.domain.statuses import ListingStatus
from listings.models import Crop
from listings.models import Product
from orders.domain.statuses import OrderStatus
from users.models import User


class OrdersApiTests(APITestCase):
    """End-to-end tests for order lifecycle workflows."""

    def setUp(self):
        """Create users and products for order workflow tests."""
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
        self.seller_one = User.objects.create_user(
            email='seller1@example.com',
            full_name='Seller One',
            password='StrongPass123',
            role='seller',
            is_active=True,
        )
        self.seller_two = User.objects.create_user(
            email='seller2@example.com',
            full_name='Seller Two',
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
        self.crop = Crop.objects.create(name='Onion', slug='onion')
        self.product_one = Product.objects.create(
            seller=self.seller_one,
            crop=self.crop,
            title='Yellow Onion',
            description='Fresh yellow onions',
            unit='kg',
            price_per_unit='10.00',
            quantity_available='200.000',
            minimum_order_quantity='5.000',
            location_name='Johannesburg',
            expires_at=timezone.now() + timedelta(days=10),
            status=ListingStatus.ACTIVE,
        )
        self.product_two = Product.objects.create(
            seller=self.seller_two,
            crop=self.crop,
            title='Red Onion',
            description='Fresh red onions',
            unit='kg',
            price_per_unit='12.00',
            quantity_available='150.000',
            minimum_order_quantity='3.000',
            location_name='Pretoria',
            expires_at=timezone.now() + timedelta(days=10),
            status=ListingStatus.ACTIVE,
        )

    def _create_order(self):
        """Create a standard multi-seller order and return response payload."""
        self.client.force_authenticate(user=self.buyer)
        response = self.client.post(
            reverse('orders:buyer-orders'),
            data={
                'items': [
                    {'product_id': self.product_one.id, 'quantity': '20.000'},
                    {'product_id': self.product_two.id, 'quantity': '10.000'},
                ],
                'notes': 'Handle with care',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.data

    def test_create_order_allocates_multi_seller_items(self):
        """Creating order should allocate items and deduct listing inventory."""
        order = self._create_order()

        self.assertEqual(order['status'], OrderStatus.PENDING)
        self.assertEqual(order['seller_count'], 2)
        self.assertEqual(order['item_count'], 2)
        self.assertEqual(order['subtotal_amount'], '320.00')

        self.product_one.refresh_from_db()
        self.product_two.refresh_from_db()
        self.assertEqual(str(self.product_one.quantity_available), '180.000')
        self.assertEqual(str(self.product_two.quantity_available), '140.000')

    def test_confirm_and_fulfill_items_completes_order(self):
        """Confirmed order should complete when all allocated items are fulfilled."""
        order = self._create_order()
        order_id = order['id']

        confirm = self.client.post(reverse('orders:confirm', kwargs={'order_id': order_id}), format='json')
        self.assertEqual(confirm.status_code, status.HTTP_200_OK)
        self.assertEqual(confirm.data['status'], OrderStatus.CONFIRMED)

        item_one = confirm.data['items'][0]
        item_two = confirm.data['items'][1]

        self.client.force_authenticate(user=self.seller_one)
        first_fulfill = self.client.post(
            reverse(
                'orders:fulfill-item',
                kwargs={'order_id': order_id, 'item_id': item_one['id']},
            ),
            format='json',
        )
        self.assertEqual(first_fulfill.status_code, status.HTTP_200_OK)
        self.assertEqual(first_fulfill.data['status'], OrderStatus.CONFIRMED)

        self.client.force_authenticate(user=self.seller_two)
        second_fulfill = self.client.post(
            reverse(
                'orders:fulfill-item',
                kwargs={'order_id': order_id, 'item_id': item_two['id']},
            ),
            format='json',
        )
        self.assertEqual(second_fulfill.status_code, status.HTTP_200_OK)
        self.assertEqual(second_fulfill.data['status'], OrderStatus.COMPLETED)

    def test_cancellation_rules_and_restock(self):
        """Buyer can cancel pending orders and admin can cancel confirmed orders."""
        first_order = self._create_order()
        cancel_pending = self.client.post(
            reverse('orders:cancel', kwargs={'order_id': first_order['id']}),
            data={'reason': 'Changed my mind'},
            format='json',
        )
        self.assertEqual(cancel_pending.status_code, status.HTTP_200_OK)
        self.assertEqual(cancel_pending.data['status'], OrderStatus.CANCELLED)

        self.product_one.refresh_from_db()
        self.product_two.refresh_from_db()
        self.assertEqual(str(self.product_one.quantity_available), '200.000')
        self.assertEqual(str(self.product_two.quantity_available), '150.000')

        second_order = self._create_order()
        self.client.post(reverse('orders:confirm', kwargs={'order_id': second_order['id']}), format='json')

        buyer_cancel_confirmed = self.client.post(
            reverse('orders:cancel', kwargs={'order_id': second_order['id']}),
            data={'reason': 'Cannot proceed'},
            format='json',
        )
        self.assertEqual(buyer_cancel_confirmed.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin_user)
        admin_cancel_confirmed = self.client.post(
            reverse('orders:cancel', kwargs={'order_id': second_order['id']}),
            data={'reason': 'Admin intervention'},
            format='json',
        )
        self.assertEqual(admin_cancel_confirmed.status_code, status.HTTP_200_OK)
        self.assertEqual(admin_cancel_confirmed.data['status'], OrderStatus.CANCELLED)

    def test_order_access_controls(self):
        """Only participants or admin can access order details."""
        order = self._create_order()
        order_id = order['id']

        self.client.force_authenticate(user=self.other_buyer)
        forbidden = self.client.get(reverse('orders:detail', kwargs={'order_id': order_id}))
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.seller_one)
        seller_view = self.client.get(reverse('orders:detail', kwargs={'order_id': order_id}))
        self.assertEqual(seller_view.status_code, status.HTTP_200_OK)

    def test_seller_order_listing(self):
        """Seller endpoint should return orders containing seller allocated items."""
        self._create_order()
        self.client.force_authenticate(user=self.seller_one)
        response = self.client.get(reverse('orders:seller-orders'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
