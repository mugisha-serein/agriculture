"""Logistics app API tests."""

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from listings.domain.statuses import ListingStatus
from listings.models import Crop, Product, ProductInventory, ProductPricing
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
            first_name='Buyer',
            last_name='One',
            password='StrongPass123',
            role='buyer',
            is_active=True,
        )
        self.seller = User.objects.create_user(
            email='seller@example.com',
            first_name='Seller',
            last_name='One',
            password='StrongPass123',
            role='seller',
            is_active=True,
        )
        self.seller.is_verified = True
        self.seller.save()
        self.transporter = User.objects.create_user(
            email='transporter@example.com',
            first_name='Transporter',
            last_name='One',
            password='StrongPass123',
            role='transporter',
            is_active=True,
        )
        self.transporter.is_verified = True
        self.transporter.save()
        self.other_user = User.objects.create_user(
            email='other@example.com',
            first_name='Other',
            last_name='User',
            password='StrongPass123',
            role='buyer',
            is_active=True,
        )
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            first_name='Admin',
            last_name='One',
            password='StrongPass123',
            role='admin',
            is_active=True,
            is_staff=True,
        )
        self.admin_user.is_verified = True
        self.admin_user.save()
        self.crop = Crop.objects.create(name='Carrot', slug='carrot')
        self.product = Product.objects.create(
            seller=self.seller,
            crop=self.crop,
            title='Orange Carrot',
            unit='kg',
            minimum_order_quantity='2.000',
            location_name='Pretoria',
            expires_at=timezone.now() + timedelta(days=7),
            status=ListingStatus.ACTIVE,
        )
        ProductInventory.objects.create(
            product=self.product,
            available_quantity='200.000',
            reserved_quantity='0.000',
        )
        ProductPricing.objects.create(
            product=self.product,
            currency='USD',
            price='8.00',
            discount='0.00',
            valid_from=timezone.now() - timedelta(days=1),
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
        self.order_two = Order.objects.create(
            order_number='ORD-LOG-0002',
            buyer=self.buyer,
            status='confirmed',
            currency='ZAR',
            subtotal_amount='50.00',
            seller_count=1,
            item_count=1,
            placed_at=timezone.now(),
            confirmed_at=timezone.now(),
        )
        OrderItem.objects.create(
            order=self.order_two,
            product=self.product,
            seller=self.seller,
            product_title=self.product.title,
            unit=self.product.unit,
            unit_price='10.00',
            quantity='5.000',
            line_total='50.00',
            status='allocated',
            allocated_at=timezone.now(),
        )

    def _create_shipment(self, *, order_id=None):
        """Create shipment as seller and return payload."""
        self.client.force_authenticate(user=self.seller)
        response = self.client.post(
            reverse('logistics:shipments'),
            data={
                'order_id': order_id or self.order.id,
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

        out_for_delivery = self.client.post(
            reverse('logistics:status', kwargs={'shipment_id': shipment_id}),
            data={'status': ShipmentStatus.OUT_FOR_DELIVERY, 'location_note': 'Entering city'},
            format='json',
        )
        self.assertEqual(out_for_delivery.status_code, status.HTTP_200_OK)
        self.assertEqual(out_for_delivery.data['status'], ShipmentStatus.OUT_FOR_DELIVERY)

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

    def test_tracking_event_endpoint_records_event(self):
        """Transporter can send GPS telemetry for a shipment."""
        shipment = self._create_shipment()
        assigned = self._assign_shipment(shipment_id=shipment['id'])
        shipment_id = assigned['id']
        self.client.force_authenticate(user=self.transporter)
        response = self.client.post(
            reverse('logistics:tracking', kwargs={'shipment_id': shipment_id}),
            data={
                'lat': '-26.204100',
                'lng': '28.047300',
                'status': ShipmentStatus.PICKED_UP,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], ShipmentStatus.PICKED_UP)

    def test_route_planning_creates_capacity_bound_routes(self):
        """Admin can plan delivery routes that chunk shipments."""
        first_shipment = self._create_shipment(order_id=self.order.id)
        second_shipment = self._create_shipment(order_id=self.order_two.id)
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            reverse('logistics:route-plan'),
            data={
                'shipment_ids': [first_shipment['id'], second_shipment['id']],
                'vehicle_identifier': 'Truck 27',
                'driver_name': 'Route Driver',
                'capacity': 1,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['shipment_items'][0]['shipment_reference'], first_shipment['shipment_reference'])
