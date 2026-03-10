"""Logistics app API tests."""

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from listings.domain.statuses import ListingStatus
from listings.models import Crop
from listings.models import Product
from logistics.domain.statuses import ShipmentStatus
from orders.models import Order
from orders.models import OrderItem
from users.models import User


class LogisticsApiTests(APITestCase):
    """End-to-end tests for shipment coordination workflows."""

    def setUp(self):
        """Create fixtures for logistics flow tests."""
        self.buyer = User.objects.create_user(
            email='buyer@example.com',
            full_name='Buyer One',
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
        self.transporter = User.objects.create_user(
            email='transporter@example.com',
            full_name='Transporter One',
            password='StrongPass123',
            role='transporter',
            is_active=True,
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            full_name='Other User',
            password='StrongPass123',
            role='buyer',
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
        self.crop = Crop.objects.create(name='Carrot', slug='carrot')
        self.product = Product.objects.create(
            seller=self.seller,
            crop=self.crop,
            title='Orange Carrot',
            unit='kg',
            price_per_unit='8.00',
            quantity_available='200.000',
            minimum_order_quantity='2.000',
            location_name='Pretoria',
            expires_at=timezone.now() + timedelta(days=7),
            status=ListingStatus.ACTIVE,
        )
        self.order = Order.objects.create(
            order_number='ORD-LOG-0001',
            buyer=self.buyer,
            status='confirmed',
            currency='ZAR',
            subtotal_amount='80.00',
            seller_count=1,
            item_count=1,
            placed_at=timezone.now(),
            confirmed_at=timezone.now(),
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            seller=self.seller,
            product_title=self.product.title,
            unit=self.product.unit,
            unit_price='8.00',
            quantity='10.000',
            line_total='80.00',
            status='allocated',
            allocated_at=timezone.now(),
        )

    def _create_shipment(self):
        """Create shipment as seller and return payload."""
        self.client.force_authenticate(user=self.seller)
        response = self.client.post(
            reverse('logistics:shipments'),
            data={
                'order_id': self.order.id,
                'seller_id': self.seller.id,
                'pickup_address': 'Farm 12, Pretoria',
                'delivery_address': 'Market 4, Johannesburg',
                'scheduled_pickup_at': (timezone.now() + timedelta(hours=6)).isoformat(),
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.data

    def _assign_shipment(self, shipment_id):
        """Assign transporter as admin and return payload."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            reverse('logistics:assign', kwargs={'shipment_id': shipment_id}),
            data={'transporter_id': self.transporter.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data

    def test_create_and_assign_shipment(self):
        """Seller can create shipment and admin can assign transporter."""
        shipment = self._create_shipment()
        assigned = self._assign_shipment(shipment_id=shipment['id'])
        self.assertEqual(assigned['status'], ShipmentStatus.ASSIGNED)
        self.assertEqual(assigned['transporter_id'], self.transporter.id)

    def test_transporter_tracking_flow_and_delivery_confirmation(self):
        """Transporter can progress tracking states and buyer can confirm delivery."""
        shipment = self._create_shipment()
        assigned = self._assign_shipment(shipment_id=shipment['id'])
        shipment_id = assigned['id']

        self.client.force_authenticate(user=self.transporter)
        picked_up = self.client.post(
            reverse('logistics:status', kwargs={'shipment_id': shipment_id}),
            data={'status': ShipmentStatus.PICKED_UP, 'location_note': 'Loaded at farm'},
            format='json',
        )
        self.assertEqual(picked_up.status_code, status.HTTP_200_OK)
        self.assertEqual(picked_up.data['status'], ShipmentStatus.PICKED_UP)

        in_transit = self.client.post(
            reverse('logistics:status', kwargs={'shipment_id': shipment_id}),
            data={'status': ShipmentStatus.IN_TRANSIT, 'location_note': 'N1 highway'},
            format='json',
        )
        self.assertEqual(in_transit.status_code, status.HTTP_200_OK)
        self.assertEqual(in_transit.data['status'], ShipmentStatus.IN_TRANSIT)

        delivered = self.client.post(
            reverse('logistics:status', kwargs={'shipment_id': shipment_id}),
            data={
                'status': ShipmentStatus.DELIVERED,
                'location_note': 'Arrived at destination',
                'delivery_proof': 'Receiver signature: John',
            },
            format='json',
        )
        self.assertEqual(delivered.status_code, status.HTTP_200_OK)
        self.assertEqual(delivered.data['status'], ShipmentStatus.DELIVERED)

        self.client.force_authenticate(user=self.buyer)
        confirmed = self.client.post(
            reverse('logistics:confirm-delivery', kwargs={'shipment_id': shipment_id}),
            data={'confirmation_note': 'Goods received in good condition'},
            format='json',
        )
        self.assertEqual(confirmed.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(confirmed.data['delivery_confirmed_at'])

    def test_invalid_status_transition_is_blocked(self):
        """Invalid shipment transition should return validation error."""
        shipment = self._create_shipment()
        assigned = self._assign_shipment(shipment_id=shipment['id'])

        self.client.force_authenticate(user=self.transporter)
        invalid = self.client.post(
            reverse('logistics:status', kwargs={'shipment_id': assigned['id']}),
            data={'status': ShipmentStatus.IN_TRANSIT},
            format='json',
        )
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)

    def test_access_controls_for_shipment_detail(self):
        """Only shipment participants or admin can access details."""
        shipment = self._create_shipment()
        shipment_id = shipment['id']

        self.client.force_authenticate(user=self.other_user)
        forbidden = self.client.get(reverse('logistics:shipment-detail', kwargs={'shipment_id': shipment_id}))
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.buyer)
        allowed = self.client.get(reverse('logistics:shipment-detail', kwargs={'shipment_id': shipment_id}))
        self.assertEqual(allowed.status_code, status.HTTP_200_OK)

    def test_duplicate_active_shipment_for_same_order_seller_is_blocked(self):
        """Only one non-cancelled shipment per order and seller should be allowed."""
        self._create_shipment()

        self.client.force_authenticate(user=self.seller)
        duplicate = self.client.post(
            reverse('logistics:shipments'),
            data={
                'order_id': self.order.id,
                'seller_id': self.seller.id,
                'pickup_address': 'Farm 12, Pretoria',
                'delivery_address': 'Market 4, Johannesburg',
            },
            format='json',
        )
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
