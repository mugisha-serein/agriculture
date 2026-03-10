"""Orders domain models for order aggregates and line items."""

from django.conf import settings
from django.db import models
from django.utils import timezone

from orders.domain.statuses import OrderItemStatus
from orders.domain.statuses import OrderStatus


class TimestampedModel(models.Model):
    """Abstract model with standard audit timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Order(TimestampedModel):
    """Order aggregate root for buyer purchase lifecycle."""

    order_number = models.CharField(max_length=32, unique=True)
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='purchase_orders',
    )
    status = models.CharField(max_length=16, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    currency = models.CharField(max_length=8, default='ZAR')
    subtotal_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    seller_count = models.PositiveIntegerField(default=0)
    item_count = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    placed_at = models.DateTimeField(default=timezone.now)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    cancellation_reason = models.TextField(blank=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-placed_at']

    def __str__(self):
        """Return human-readable order reference."""
        return self.order_number


class OrderItem(TimestampedModel):
    """Order line item allocated to a specific seller listing."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('listings.Product', on_delete=models.PROTECT, related_name='order_items')
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='sales_order_items',
    )
    product_title = models.CharField(max_length=160)
    unit = models.CharField(max_length=16)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    line_total = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(
        max_length=16,
        choices=OrderItemStatus.choices,
        default=OrderItemStatus.ALLOCATED,
    )
    allocated_at = models.DateTimeField(default=timezone.now)
    fulfilled_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'order_items'
        ordering = ['id']

    def __str__(self):
        """Return readable line item identifier."""
        return f'{self.order.order_number}:{self.id}'
