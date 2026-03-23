"""Audit app tests for system-wide traceability guarantees."""

from decimal import Decimal
from datetime import timedelta

from django.core.exceptions import ValidationError as DjangoValidationError
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from audit.domain.alerts import AlertSeverity
from audit.domain.alerts import AlertType
from audit.domain.audiences import AuditAudience
from audit.models import AuditAlert
from audit.models import AuditEvent
from audit.models import AuditRequestAction
from payments.models import EscrowTransaction
from payments.models import Payment
from listings.models import Crop, Product, ProductInventory, ProductPricing
from orders.domain.statuses import OrderStatus
from orders.models import Order
from users.models import User


class AuditabilityTests(APITestCase):
    """End-to-end tests for immutable cross-domain auditability."""

    def setUp(self):
        """Create baseline users and listing fixtures."""
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            first_name='Admin',
            last_name='One',
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
        self.seller.is_verified = True
        self.seller.save()
        self.buyer = User.objects.create_user(
            email='buyer@example.com',
            first_name='Buyer',
            last_name='One',
            password='StrongPass123',
            role='buyer',
            is_active=True,
        )
        self.crop = Crop.objects.create(name='Tomato', slug='tomato')
        self.product = Product.objects.create(
            seller=self.seller,
            crop=self.crop,
            title='Red Tomato',
            unit='kg',
            minimum_order_quantity='2.000',
            location_name='Johannesburg',
            expires_at=timezone.now() + timedelta(days=10),
            status='active',
        )
        ProductInventory.objects.create(
            product=self.product,
            available_quantity='100.000',
            reserved_quantity='0.000',
        )
        ProductPricing.objects.create(
            product=self.product,
            currency='USD',
            price='6.00',
            discount='0.00',
            valid_from=timezone.now() - timedelta(days=1),
        )
        self.order = Order.objects.create(
            order_number='ORD-AUDIT-0001',
            buyer=self.buyer,
            status=OrderStatus.COMPLETED,
            currency='ZAR',
            subtotal_amount='50.00',
            seller_count=1,
            item_count=1,
            placed_at=timezone.now(),
            confirmed_at=timezone.now(),
            completed_at=timezone.now(),
        )

    def test_request_actor_and_changes_are_audited(self):
        """Product updates should record actor, request metadata, and changed fields."""
        baseline_id = AuditEvent.objects.order_by('-id').values_list('id', flat=True).first() or 0
        request_id = 'req-audit-001'

        self.client.force_authenticate(user=self.seller)
        response = self.client.patch(
            reverse('marketplace:product-detail', kwargs={'product_id': self.product.id}),
            data={'available_quantity': '90.000'},
            format='json',
            HTTP_X_REQUEST_ID=request_id,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.headers.get('X-Request-ID'), request_id)

        inventory_id = self.product.inventory.id
        event = (
            AuditEvent.objects.filter(
                id__gt=baseline_id,
                model_label='listings.ProductInventory',
                object_pk=str(inventory_id),
                action='update',
            )
            .order_by('-id')
            .first()
        )
        self.assertIsNotNone(event)
        self.assertEqual(event.actor_id, self.seller.id)
        self.assertEqual(event.request_id, request_id)
        self.assertEqual(event.request_method, 'PATCH')
        self.assertEqual(event.request_path, f'/api/marketplace/products/{self.product.id}/')
        self.assertIn('available_quantity', event.change_set)

    def test_delete_operation_is_audited(self):
        """Model delete operations should write immutable delete audit events."""
        crop = Crop.objects.create(name='Temporary Crop', slug='temporary-crop')
        crop_id = crop.id
        crop.delete()

        event = AuditEvent.objects.filter(
            model_label='listings.Crop',
            object_pk=str(crop_id),
            action='delete',
        ).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.after_state, {})
        self.assertEqual(event.before_state['name'], 'Temporary Crop')

    def test_audit_events_are_immutable(self):
        """Audit events cannot be edited or deleted after persistence."""
        event = AuditEvent.objects.order_by('-id').first()
        event.actor_email = 'tampered@example.com'
        with self.assertRaises(DjangoValidationError):
            event.save()
        with self.assertRaises(DjangoValidationError):
            event.delete()

    def test_audit_api_is_admin_only(self):
        """Audit event API should be accessible only by admin users."""
        self.client.force_authenticate(user=self.seller)
        forbidden = self.client.get(reverse('audit:events'))
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin_user)
        allowed = self.client.get(reverse('audit:events'))
        self.assertEqual(allowed.status_code, status.HTTP_200_OK)
        self.assertIn('results', allowed.data)

    def test_required_app_actions_are_all_logged(self):
        """Request actions should be logged for all required monitored app scopes."""
        initial_id = AuditRequestAction.objects.order_by('-id').values_list('id', flat=True).first() or 0

        self.client.get('/api/payments/')
        self.client.get('/api/orders/')
        self.client.get('/api/logistics/shipments/')
        self.client.get('/api/marketplace/products/')
        self.client.get('/api/verification/me/')
        self.client.post(
            '/api/identity/login/',
            data={'email': self.seller.email, 'password': 'StrongPass123'},
            format='json',
        )

        scopes = set(
            AuditRequestAction.objects.filter(id__gt=initial_id).values_list('app_scope', flat=True)
        )
        self.assertTrue(
            {'payments', 'orders', 'logistics', 'listings', 'verification', 'last_login'}.issubset(
                scopes
            )
        )
        last_login_action = (
            AuditRequestAction.objects.filter(id__gt=initial_id, app_scope='last_login')
            .order_by('-id')
            .first()
        )
        self.assertIsNotNone(last_login_action)
        self.assertEqual(last_login_action.action_name, 'last_login')

    def test_last_login_model_event_is_logged(self):
        """Successful login should generate dedicated last_login model audit event."""
        initial_id = AuditEvent.objects.order_by('-id').values_list('id', flat=True).first() or 0
        response = self.client.post(
            '/api/identity/login/',
            data={'email': self.seller.email, 'password': 'StrongPass123'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        event = (
            AuditEvent.objects.filter(
                id__gt=initial_id,
                model_label='users.User',
                source='last_login',
                action='custom',
            )
            .order_by('-id')
            .first()
        )
        self.assertIsNotNone(event)
        self.assertIn('last_login', event.change_set)

    def test_request_action_management_is_admin_only(self):
        """Only admin can manage request action workflow state."""
        self.client.get('/api/payments/')
        action = AuditRequestAction.objects.filter(app_scope='payments').order_by('-id').first()
        self.assertIsNotNone(action)

        self.client.force_authenticate(user=self.seller)
        forbidden = self.client.post(
            reverse('audit:manage-action', kwargs={'action_id': action.id}),
            data={'management_status': 'in_review', 'management_note': 'Check payment flow'},
            format='json',
        )
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin_user)
        allowed = self.client.post(
            reverse('audit:manage-action', kwargs={'action_id': action.id}),
            data={'management_status': 'resolved', 'management_note': 'Verified and closed'},
            format='json',
        )
        self.assertEqual(allowed.status_code, status.HTTP_200_OK)
        self.assertEqual(allowed.data['management_status'], 'resolved')
        self.assertEqual(allowed.data['management_note'], 'Verified and closed')

        listing = self.client.get(
            reverse('audit:actions'),
            data={'app_scope': 'payments', 'management_status': 'resolved'},
        )
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(listing.data['pagination']['total_count'], 1)

    def test_admin_privilege_change_triggers_alert(self):
        """Promoting a user to admin should emit a critical audit alert."""
        self.seller.role = 'admin'
        self.seller.is_staff = True
        self.seller.save()

        alert = AuditAlert.objects.filter(
            event__model_label='users.User',
            event__object_pk=str(self.seller.id),
            alert_type=AlertType.ADMIN_PRIVILEGE_CHANGE,
        ).order_by('-id').first()
        self.assertIsNotNone(alert)
        self.assertEqual(alert.severity, AlertSeverity.CRITICAL)

    def test_account_suspension_triggers_alert(self):
        """Disabling a user should be captured by the alert pipeline."""
        self.seller.is_active = False
        self.seller.save()

        alert = AuditAlert.objects.filter(
            event__model_label='users.User',
            alert_type=AlertType.ACCOUNT_SUSPENSION,
        ).order_by('-id').first()
        self.assertIsNotNone(alert)
        self.assertEqual(alert.severity, AlertSeverity.WARNING)

    def test_large_refund_alert_is_logged(self):
        """Refund transactions above the threshold generate critical alerts."""
        payment = Payment.objects.create(
            payment_reference='PAY-EXPORT-001',
            order=self.order,
            buyer=self.buyer,
            status='refunded',
            amount='5000.00',
            currency='ZAR',
            idempotency_key='refund-limit',
            request_fingerprint='refund-limit',
            provider='mock_gateway',
        )
        EscrowTransaction.objects.create(
            payment=payment,
            transaction_type='refund',
            amount=Decimal('5000.00'),
            currency='ZAR',
        )

        alert = AuditAlert.objects.filter(
            alert_type=AlertType.LARGE_REFUND,
        ).order_by('-id').first()
        self.assertIsNotNone(alert)
        self.assertEqual(alert.severity, AlertSeverity.CRITICAL)

    def test_audit_export_endpoint_returns_payload(self):
        """Admins can request audit_exports payload for regulated audiences."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(reverse('audit:exports'), data={'audience': AuditAudience.REGULATORS})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['audience'], AuditAudience.REGULATORS)
        self.assertIn('events', response.data)
