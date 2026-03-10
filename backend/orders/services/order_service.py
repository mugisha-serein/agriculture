"""Order workflows for creation, allocation, and lifecycle transitions."""

from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError

from listings.domain.statuses import ListingStatus
from listings.models import Product
from orders.domain.statuses import OrderItemStatus
from orders.domain.statuses import OrderStatus
from orders.models import Order
from orders.models import OrderItem


class OrderService:
    """Application service for order domain operations."""

    @transaction.atomic
    def create_order(self, *, actor, items, notes=''):
        """Create an order and allocate quantities across one or more sellers."""
        self._assert_buyer_or_admin(actor)
        normalized_items = self._normalize_items(items)
        product_ids = [item['product_id'] for item in normalized_items]
        products = (
            Product.objects.select_for_update()
            .select_related('seller', 'crop')
            .filter(id__in=product_ids)
        )
        products_by_id = {product.id: product for product in products}
        if len(products_by_id) != len(product_ids):
            missing = sorted(set(product_ids) - set(products_by_id.keys()))
            raise ValidationError({'items': [f'Unknown product ids: {missing}']})

        now = timezone.now()
        today = timezone.localdate()
        order = Order.objects.create(
            order_number=self._generate_order_number(),
            buyer=actor,
            status=OrderStatus.PENDING,
            notes=notes,
            placed_at=now,
        )

        subtotal_amount = Decimal('0.00')
        seller_ids = set()
        item_records = []
        for item in normalized_items:
            product = products_by_id[item['product_id']]
            quantity = item['quantity']
            self._assert_orderable_product(product=product, now=now, today=today, quantity=quantity)
            line_total = (quantity * product.price_per_unit).quantize(
                Decimal('0.01'),
                rounding=ROUND_HALF_UP,
            )
            item_record = OrderItem.objects.create(
                order=order,
                product=product,
                seller=product.seller,
                product_title=product.title,
                unit=product.unit,
                unit_price=product.price_per_unit,
                quantity=quantity,
                line_total=line_total,
                status=OrderItemStatus.ALLOCATED,
                allocated_at=now,
            )
            item_records.append(item_record)
            seller_ids.add(product.seller_id)
            subtotal_amount += line_total

            product.quantity_available = (product.quantity_available - quantity).quantize(
                Decimal('0.001'),
                rounding=ROUND_HALF_UP,
            )
            if product.quantity_available <= 0:
                product.quantity_available = Decimal('0.000')
                product.status = ListingStatus.SOLD_OUT
            product.save(update_fields=['quantity_available', 'status', 'updated_at'])

        order.subtotal_amount = subtotal_amount
        order.seller_count = len(seller_ids)
        order.item_count = len(item_records)
        order.save(update_fields=['subtotal_amount', 'seller_count', 'item_count', 'updated_at'])
        return self.get_order(actor=actor, order_id=order.id)

    def list_buyer_orders(self, *, actor, status=None):
        """List orders placed by the authenticated buyer."""
        if not actor.is_authenticated:
            raise PermissionDenied('Authentication is required.')
        queryset = Order.objects.filter(buyer=actor).prefetch_related('items')
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def list_seller_orders(self, *, actor, status=None):
        """List orders containing items allocated to the authenticated seller."""
        if not actor.is_authenticated:
            raise PermissionDenied('Authentication is required.')
        if not (actor.is_staff or getattr(actor, 'role', None) == 'admin'):
            if getattr(actor, 'role', None) != 'seller':
                raise PermissionDenied('Only sellers can access seller orders.')
            queryset = Order.objects.filter(items__seller=actor).distinct().prefetch_related('items')
        else:
            queryset = Order.objects.all().prefetch_related('items')
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_order(self, *, actor, order_id):
        """Return order details if the actor participates in the order."""
        try:
            order = Order.objects.prefetch_related('items__seller', 'items__product').get(id=order_id)
        except Order.DoesNotExist as exc:
            raise NotFound('Order was not found.') from exc
        self._assert_order_access(actor=actor, order=order)
        return order

    @transaction.atomic
    def confirm_order(self, *, actor, order_id):
        """Transition an order from pending to confirmed."""
        order = self._get_locked_order(order_id=order_id)
        if actor.id != order.buyer_id and not self._is_admin(actor):
            raise PermissionDenied('Only the buyer or admin can confirm this order.')
        if order.status != OrderStatus.PENDING:
            raise ValidationError({'status': ['Only pending orders can be confirmed.']})
        order.status = OrderStatus.CONFIRMED
        order.confirmed_at = timezone.now()
        order.save(update_fields=['status', 'confirmed_at', 'updated_at'])
        return self.get_order(actor=actor, order_id=order_id)

    @transaction.atomic
    def cancel_order(self, *, actor, order_id, reason):
        """Cancel an order according to buyer and admin cancellation rules."""
        if not reason.strip():
            raise ValidationError({'reason': ['Cancellation reason is required.']})
        order = self._get_locked_order(order_id=order_id)
        if not self._can_cancel(actor=actor, order=order):
            raise PermissionDenied('You cannot cancel this order in its current state.')
        if order.status not in {OrderStatus.PENDING, OrderStatus.CONFIRMED}:
            raise ValidationError({'status': ['Only pending or confirmed orders can be cancelled.']})

        items = list(
            OrderItem.objects.select_for_update()
            .select_related('product')
            .filter(order=order)
        )
        now = timezone.now()
        self._restock_allocated_items(items=items, now=now)

        OrderItem.objects.filter(
            order=order,
            status=OrderItemStatus.ALLOCATED,
        ).update(status=OrderItemStatus.CANCELLED, cancelled_at=now, updated_at=now)

        order.status = OrderStatus.CANCELLED
        order.cancelled_at = now
        order.cancellation_reason = reason
        order.save(update_fields=['status', 'cancelled_at', 'cancellation_reason', 'updated_at'])
        return self.get_order(actor=actor, order_id=order_id)

    @transaction.atomic
    def fulfill_order_item(self, *, actor, order_id, item_id):
        """Mark one order item fulfilled by its seller or admin."""
        order = self._get_locked_order(order_id=order_id)
        if order.status != OrderStatus.CONFIRMED:
            raise ValidationError({'status': ['Only confirmed orders can be fulfilled.']})

        try:
            item = (
                OrderItem.objects.select_for_update()
                .select_related('seller')
                .get(id=item_id, order=order)
            )
        except OrderItem.DoesNotExist as exc:
            raise NotFound('Order item was not found.') from exc

        if not self._is_admin(actor) and actor.id != item.seller_id:
            raise PermissionDenied('Only the seller owner or admin can fulfill this item.')
        if item.status != OrderItemStatus.ALLOCATED:
            raise ValidationError({'status': ['Only allocated items can be fulfilled.']})

        item.status = OrderItemStatus.FULFILLED
        item.fulfilled_at = timezone.now()
        item.save(update_fields=['status', 'fulfilled_at', 'updated_at'])

        remaining_allocated = order.items.filter(status=OrderItemStatus.ALLOCATED).exists()
        if not remaining_allocated:
            order.status = OrderStatus.COMPLETED
            order.completed_at = timezone.now()
            order.save(update_fields=['status', 'completed_at', 'updated_at'])
        return self.get_order(actor=actor, order_id=order_id)

    def _assert_orderable_product(self, *, product, now, today, quantity):
        """Validate listing state before order allocation."""
        if product.is_deleted:
            raise ValidationError({'items': [f'Product {product.id} is not available.']})
        if product.status != ListingStatus.ACTIVE:
            raise ValidationError({'items': [f'Product {product.id} is not active.']})
        if product.available_from > today:
            raise ValidationError({'items': [f'Product {product.id} is not yet available.']})
        if product.expires_at <= now:
            raise ValidationError({'items': [f'Product {product.id} is expired.']})
        if quantity < product.minimum_order_quantity:
            raise ValidationError(
                {'items': [f'Product {product.id} requires minimum quantity {product.minimum_order_quantity}.']}
            )
        if quantity > product.quantity_available:
            raise ValidationError(
                {'items': [f'Product {product.id} has insufficient quantity available.']}
            )

    def _assert_order_access(self, *, actor, order):
        """Validate that actor can view the requested order."""
        if not actor.is_authenticated:
            raise PermissionDenied('Authentication is required.')
        if self._is_admin(actor):
            return
        if actor.id == order.buyer_id:
            return
        if order.items.filter(seller_id=actor.id).exists():
            return
        raise PermissionDenied('You do not have access to this order.')

    def _assert_buyer_or_admin(self, actor):
        """Require buyer or admin role for order placement."""
        if not actor.is_authenticated:
            raise PermissionDenied('Authentication is required.')
        if self._is_admin(actor):
            return
        if getattr(actor, 'role', None) != 'buyer':
            raise PermissionDenied('Only buyers can place orders.')

    def _can_cancel(self, *, actor, order):
        """Evaluate cancellation policy for buyer and admin actors."""
        if not actor.is_authenticated:
            return False
        if self._is_admin(actor):
            return True
        if actor.id != order.buyer_id:
            return False
        return order.status == OrderStatus.PENDING

    def _normalize_items(self, items):
        """Normalize order items and combine duplicate product requests."""
        if not items:
            raise ValidationError({'items': ['At least one item is required.']})
        merged = {}
        for item in items:
            product_id = item.get('product_id')
            quantity_raw = item.get('quantity')
            if product_id is None:
                raise ValidationError({'items': ['product_id is required for each item.']})
            if quantity_raw is None:
                raise ValidationError({'items': ['quantity is required for each item.']})
            quantity = Decimal(str(quantity_raw))
            if quantity <= 0:
                raise ValidationError({'items': ['quantity must be greater than zero.']})
            key = int(product_id)
            merged[key] = merged.get(key, Decimal('0.000')) + quantity
        return [
            {'product_id': key, 'quantity': value.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)}
            for key, value in merged.items()
        ]

    def _restock_allocated_items(self, *, items, now):
        """Return allocated quantities back to listing inventory during cancellation."""
        product_ids = [item.product_id for item in items if item.status == OrderItemStatus.ALLOCATED]
        products = Product.objects.select_for_update().filter(id__in=product_ids)
        products_by_id = {product.id: product for product in products}

        for item in items:
            if item.status != OrderItemStatus.ALLOCATED:
                continue
            product = products_by_id.get(item.product_id)
            if product is None:
                continue
            product.quantity_available = (product.quantity_available + item.quantity).quantize(
                Decimal('0.001'),
                rounding=ROUND_HALF_UP,
            )
            if (
                not product.is_deleted
                and product.expires_at > now
                and product.quantity_available > 0
                and product.status in {ListingStatus.SOLD_OUT, ListingStatus.INACTIVE, ListingStatus.EXPIRED}
            ):
                product.status = ListingStatus.ACTIVE
            product.save(update_fields=['quantity_available', 'status', 'updated_at'])

    def _generate_order_number(self):
        """Generate a unique order number identifier."""
        return f'ORD-{timezone.now().strftime("%Y%m%d")}-{uuid4().hex[:8].upper()}'

    def _is_admin(self, actor):
        """Check whether actor has administrative privileges."""
        return actor.is_staff or getattr(actor, 'role', None) == 'admin'

    def _get_locked_order(self, *, order_id):
        """Fetch and lock order row for state mutations."""
        try:
            return (
                Order.objects.select_for_update()
                .prefetch_related('items')
                .get(id=order_id)
            )
        except Order.DoesNotExist as exc:
            raise NotFound('Order was not found.') from exc
