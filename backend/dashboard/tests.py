from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from audit.domain.alerts import AlertSeverity
from audit.domain.alerts import AlertType
from audit.models import AuditAlert
from audit.models import AuditEvent
from listings.domain.statuses import ListingStatus
from listings.models import Crop, Product, ProductInventory, ProductPricing
from logistics.domain.statuses import ShipmentStatus
from logistics.models import Shipment
from orders.domain.statuses import OrderStatus
from orders.models import Order, OrderItem
from payments.domain.statuses import PaymentStatus
from payments.models import Payment
from users.models import User


class DashboardAnalyticsTests(APITestCase):
    """Analytics engine coverage for admin dashboards."""

    def setUp(self):
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            first_name='Admin',
            last_name='Analytics',
            password='StrongPass123',
            role='admin',
            is_active=True,
            is_staff=True,
        )
        self.seller = User.objects.create_user(
            email='seller@example.com',
            first_name='Seller',
            last_name='One',
            password='StrongPass123',
            role='seller',
            is_active=True,
        )
        self.buyer = User.objects.create_user(
            email='buyer@example.com',
            first_name='Buyer',
            last_name='One',
            password='StrongPass123',
            role='buyer',
            is_active=True,
        )
        crop = Crop.objects.create(name='Kale', slug='kale')
        product = Product.objects.create(
            seller=self.seller,
            crop=crop,
            title='Green Kale',
            unit='kg',
            minimum_order_quantity='1.000',
            location_name='Cape Town',
            expires_at=timezone.now() + timedelta(days=30),
            status=ListingStatus.ACTIVE,
        )
        ProductInventory.objects.create(product=product, available_quantity='100.000', reserved_quantity='0.000')
        ProductPricing.objects.create(
            product=product,
            currency='ZAR',
            price='10.00',
            discount='0.00',
            valid_from=timezone.now(),
        )
        self.order = Order.objects.create(
            order_number='ORD-ANALYTICS-01',
            buyer=self.buyer,
            status=OrderStatus.COMPLETED,
            currency='ZAR',
            subtotal_amount='100.00',
            seller_count=1,
            item_count=1,
            placed_at=timezone.now(),
            confirmed_at=timezone.now(),
            completed_at=timezone.now(),
        )
        OrderItem.objects.create(
            order=self.order,
            product=product,
            seller=self.seller,
            product_title=product.title,
            unit=product.unit,
            unit_price='10.00',
            quantity='10.000',
            line_total='100.00',
            status='fulfilled',
            allocated_at=timezone.now(),
            fulfilled_at=timezone.now(),
        )
        Shipment.objects.create(
            shipment_reference='SHP-ANALYTICS-01',
            tracking_code='TRK-ANALYTICS-01',
            order=self.order,
            seller=self.seller,
            buyer=self.buyer,
            status=ShipmentStatus.DELIVERED,
            pickup_address='Farm 1',
            delivery_address='Market 1',
            assigned_at=timezone.now(),
            picked_up_at=timezone.now(),
            in_transit_at=timezone.now(),
            delivered_at=timezone.now(),
            created_by=self.seller,
        )
        Payment.objects.create(
            payment_reference='PAY-ANALYTICS-01',
            order=self.order,
            buyer=self.buyer,
            status=PaymentStatus.RELEASED,
            amount='100.00',
            currency='ZAR',
            idempotency_key='analytics-01',
            request_fingerprint='analytics-01',
            provider='mock_gateway',
        )
        event = AuditEvent.objects.create(
            request_id='req-analytics',
            actor=self.admin_user,
            actor_email=self.admin_user.email,
            source='analytics',
            action='custom',
            app_label='dashboard',
            model_label='dashboard.DailySalesMetric',
            object_pk='1',
            object_repr='Analytics',
            request_path='/api/dashboard/analytics/',
            request_method='GET',
            ip_address='127.0.0.1',
            user_agent='test-suite',
            before_state={},
            after_state={},
            change_set={},
            metadata={},
            previous_hash='',
            event_hash='hash-analytics',
        )
        AuditAlert.objects.create(
            event=event,
            alert_type=AlertType.LARGE_REFUND,
            severity=AlertSeverity.CRITICAL,
            description='Analytics fraud sample',
            context={},
            triggered_at=timezone.now(),
        )

    def test_admin_analytics_endpoint_returns_health_and_panels(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(reverse('dashboard:dashboard-analytics'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('marketplace_health', response.data)
        self.assertIn('admin_panels', response.data)

    def test_non_admin_cannot_access_analytics(self):
        self.client.force_authenticate(user=self.seller)
        response = self.client.get(reverse('dashboard:dashboard-analytics'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
