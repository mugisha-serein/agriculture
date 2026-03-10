"""Payments workflows for idempotent initiation and escrow management."""

from decimal import Decimal
from decimal import ROUND_HALF_UP
import hashlib
import json
from uuid import uuid4

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError

from orders.models import Order
from payments.domain.statuses import EscrowTransactionType
from payments.domain.statuses import PaymentStatus
from payments.models import EscrowTransaction
from payments.models import Payment


class PaymentService:
    """Application service for payment and escrow lifecycle operations."""

    @transaction.atomic
    def initiate_payment(
        self,
        *,
        actor,
        order_id,
        idempotency_key,
        provider='mock_gateway',
        amount=None,
        currency='ZAR',
    ):
        """Create idempotent payment aggregate for a buyer order."""
        order = self._get_order(order_id=order_id)
        self._assert_buyer_or_admin_for_order(actor=actor, order=order)

        normalized_amount = self._normalize_amount(amount or order.subtotal_amount)
        if normalized_amount != self._normalize_amount(order.subtotal_amount):
            raise ValidationError({'amount': ['Payment amount must match order subtotal.']})
        if currency != order.currency:
            raise ValidationError({'currency': ['Payment currency must match order currency.']})

        buyer = order.buyer
        fingerprint = self._build_request_fingerprint(
            order_id=order.id,
            amount=normalized_amount,
            currency=currency,
            provider=provider,
        )

        existing_by_key = Payment.objects.filter(
            buyer=buyer,
            idempotency_key=idempotency_key,
        ).first()
        if existing_by_key is not None:
            if existing_by_key.request_fingerprint != fingerprint:
                raise ValidationError(
                    {'idempotency_key': ['Idempotency key reused with a different request payload.']}
                )
            return existing_by_key, False

        existing_order_payment = Payment.objects.filter(order=order).first()
        if existing_order_payment is not None:
            raise ValidationError({'order_id': ['A payment already exists for this order.']})

        payment = Payment.objects.create(
            payment_reference=self._generate_payment_reference(),
            order=order,
            buyer=buyer,
            status=PaymentStatus.INITIATED,
            amount=normalized_amount,
            currency=currency,
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint,
            provider=provider,
            provider_payment_id=f'prov-{uuid4().hex[:12]}',
            initiated_at=timezone.now(),
        )
        return payment, True

    def list_payments(self, *, actor, status=None):
        """List payments available to the requesting actor (buyer, seller, or admin)."""
        if not actor.is_authenticated:
            raise PermissionDenied('Authentication is required.')
        
        from django.db.models import Q
        queryset = Payment.objects.select_related('order', 'buyer')
        
        if self._is_admin(actor):
            pass
        else:
            # Buyers see their own payments
            # Sellers see payments for orders that contain their products
            queryset = queryset.filter(
                Q(buyer=actor) | Q(order__items__seller=actor)
            ).distinct()
            
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_payment(self, *, actor, payment_id):
        """Retrieve payment details for owner buyer, related seller, or admin."""
        try:
            payment = Payment.objects.select_related('order', 'buyer').prefetch_related(
                'escrow_transactions'
            ).get(id=payment_id)
        except Payment.DoesNotExist as exc:
            raise NotFound('Payment was not found.') from exc

        # Admin, Buyer (owner), or any Seller whose product is in the order
        if self._is_admin(actor):
            return payment
            
        if actor.id == payment.buyer_id:
            return payment
            
        if payment.order.items.filter(seller=actor).exists():
            return payment
            
        raise PermissionDenied('You do not have access to this payment.')

    @transaction.atomic
    def release_escrow(self, *, actor, payment_id, metadata=None):
        """Release held escrow funds as an admin-only operation."""
        if not self._is_admin(actor):
            raise PermissionDenied('Only admin can release escrow funds.')
        payment = self._get_locked_payment(payment_id=payment_id)
        if payment.status != PaymentStatus.ESCROW_HELD:
            raise ValidationError({'status': ['Only escrow-held payments can be released.']})

        self._create_escrow_transaction(
            payment=payment,
            transaction_type=EscrowTransactionType.RELEASE,
            amount=payment.amount,
            external_reference=f'release:{payment.payment_reference}:{uuid4().hex[:8]}',
            metadata=metadata or {},
            created_by=actor,
        )
        payment.status = PaymentStatus.RELEASED
        payment.released_at = timezone.now()
        payment.save(update_fields=['status', 'released_at', 'updated_at'])
        return payment

    @transaction.atomic
    def refund_payment(self, *, actor, payment_id, reason):
        """Refund held escrow funds to buyer with strict transition checks."""
        payment = self._get_locked_payment(payment_id=payment_id)
        if not self._is_admin(actor) and actor.id != payment.buyer_id:
            raise PermissionDenied('Only payment owner or admin can request a refund.')
        if payment.status != PaymentStatus.ESCROW_HELD:
            raise ValidationError({'status': ['Only escrow-held payments can be refunded.']})
        if not reason.strip():
            raise ValidationError({'reason': ['Refund reason is required.']})

        self._create_escrow_transaction(
            payment=payment,
            transaction_type=EscrowTransactionType.REFUND,
            amount=payment.amount,
            external_reference=f'refund:{payment.payment_reference}:{uuid4().hex[:8]}',
            metadata={'reason': reason},
            created_by=actor,
        )
        payment.status = PaymentStatus.REFUNDED
        payment.refunded_at = timezone.now()
        payment.save(update_fields=['status', 'refunded_at', 'updated_at'])
        return payment

    @transaction.atomic
    def process_webhook_event(
        self,
        *,
        event_id,
        event_type,
        payment_reference,
        amount=None,
        currency=None,
        failure_code='',
        failure_message='',
        metadata=None,
    ):
        """Process provider webhook events with idempotent handling."""
        payment = self._get_locked_payment_by_reference(payment_reference=payment_reference)
        if event_id in payment.processed_webhook_ids:
            return payment, False

        normalized_amount = self._normalize_amount(amount or payment.amount)
        if normalized_amount != self._normalize_amount(payment.amount):
            raise ValidationError({'amount': ['Webhook amount mismatch for payment reference.']})
        if currency is not None and currency != payment.currency:
            raise ValidationError({'currency': ['Webhook currency mismatch for payment reference.']})

        payload_metadata = metadata or {}
        if event_type == 'payment.captured':
            if payment.status in {PaymentStatus.RELEASED, PaymentStatus.REFUNDED}:
                raise ValidationError({'status': ['Cannot capture a finalized payment.']})
            if payment.status != PaymentStatus.ESCROW_HELD:
                self._create_escrow_transaction(
                    payment=payment,
                    transaction_type=EscrowTransactionType.HOLD,
                    amount=payment.amount,
                    external_reference=event_id,
                    metadata=payload_metadata,
                    created_by=None,
                )
                payment.status = PaymentStatus.ESCROW_HELD
                payment.escrow_held_at = timezone.now()

        elif event_type == 'payment.failed':
            if payment.status in {PaymentStatus.RELEASED, PaymentStatus.REFUNDED}:
                raise ValidationError({'status': ['Cannot fail a finalized payment.']})
            payment.status = PaymentStatus.FAILED
            payment.failure_code = failure_code
            payment.failure_message = failure_message

        elif event_type == 'payout.released':
            if payment.status != PaymentStatus.ESCROW_HELD:
                raise ValidationError({'status': ['Only escrow-held payments can be released.']})
            self._create_escrow_transaction(
                payment=payment,
                transaction_type=EscrowTransactionType.RELEASE,
                amount=payment.amount,
                external_reference=event_id,
                metadata=payload_metadata,
                created_by=None,
            )
            payment.status = PaymentStatus.RELEASED
            payment.released_at = timezone.now()

        elif event_type == 'payment.refunded':
            if payment.status != PaymentStatus.ESCROW_HELD:
                raise ValidationError({'status': ['Only escrow-held payments can be refunded.']})
            self._create_escrow_transaction(
                payment=payment,
                transaction_type=EscrowTransactionType.REFUND,
                amount=payment.amount,
                external_reference=event_id,
                metadata=payload_metadata,
                created_by=None,
            )
            payment.status = PaymentStatus.REFUNDED
            payment.refunded_at = timezone.now()

        else:
            raise ValidationError({'event_type': ['Unsupported webhook event type.']})

        payment.processed_webhook_ids = [*payment.processed_webhook_ids, event_id]
        payment.save(
            update_fields=[
                'status',
                'escrow_held_at',
                'released_at',
                'refunded_at',
                'failure_code',
                'failure_message',
                'processed_webhook_ids',
                'updated_at',
            ]
        )
        return payment, True

    def _create_escrow_transaction(
        self,
        *,
        payment,
        transaction_type,
        amount,
        external_reference,
        metadata,
        created_by,
    ):
        """Create immutable escrow ledger entry."""
        return EscrowTransaction.objects.create(
            payment=payment,
            transaction_type=transaction_type,
            amount=self._normalize_amount(amount),
            currency=payment.currency,
            external_reference=external_reference,
            metadata=metadata,
            created_by=created_by,
            created_at=timezone.now(),
        )

    def _get_order(self, *, order_id):
        """Return order aggregate by identifier."""
        try:
            return Order.objects.select_related('buyer').get(id=order_id)
        except Order.DoesNotExist as exc:
            raise NotFound('Order was not found.') from exc

    def _get_locked_payment(self, *, payment_id):
        """Fetch and lock payment row for mutation."""
        try:
            return Payment.objects.select_for_update().select_related('order', 'buyer').get(id=payment_id)
        except Payment.DoesNotExist as exc:
            raise NotFound('Payment was not found.') from exc

    def _get_locked_payment_by_reference(self, *, payment_reference):
        """Fetch and lock payment by payment reference."""
        try:
            return (
                Payment.objects.select_for_update()
                .select_related('order', 'buyer')
                .get(payment_reference=payment_reference)
            )
        except Payment.DoesNotExist as exc:
            raise NotFound('Payment was not found.') from exc

    def _assert_buyer_or_admin_for_order(self, *, actor, order):
        """Enforce buyer ownership or admin rights for payment initiation."""
        if not actor.is_authenticated:
            raise PermissionDenied('Authentication is required.')
        if self._is_admin(actor):
            return
        if actor.id != order.buyer_id:
            raise PermissionDenied('Only the order buyer can initiate payment.')

    def _is_admin(self, actor):
        """Return whether actor has administrative privileges."""
        return actor.is_staff or getattr(actor, 'role', None) == 'admin'

    def _normalize_amount(self, value):
        """Normalize monetary value to two decimal places."""
        return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def _build_request_fingerprint(self, *, order_id, amount, currency, provider):
        """Build deterministic fingerprint used for idempotency checks."""
        payload = {
            'order_id': order_id,
            'amount': str(self._normalize_amount(amount)),
            'currency': currency,
            'provider': provider,
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

    def _generate_payment_reference(self):
        """Generate unique human-readable payment reference."""
        return f'PAY-{timezone.now().strftime("%Y%m%d")}-{uuid4().hex[:10].upper()}'
