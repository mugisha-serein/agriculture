"""Serializers for orders API endpoints."""

from rest_framework import serializers

from orders.domain.statuses import OrderStatus
from orders.models import Order
from orders.models import OrderItem


class OrderItemCreateSerializer(serializers.Serializer):
    """Input serializer for order item creation payload."""

    product_id = serializers.IntegerField()
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3)


class OrderCreateSerializer(serializers.Serializer):
    """Input serializer for order creation requests."""

    items = OrderItemCreateSerializer(many=True, allow_empty=False)
    notes = serializers.CharField(required=False, allow_blank=True)


class OrderCancelSerializer(serializers.Serializer):
    """Input serializer for order cancellation requests."""

    reason = serializers.CharField()


class OrderListQuerySerializer(serializers.Serializer):
    """Query serializer for order list filtering."""

    status = serializers.ChoiceField(choices=OrderStatus.choices, required=False)


class OrderItemSerializer(serializers.ModelSerializer):
    """Output serializer for order line items."""

    product_id = serializers.IntegerField(source='product.id', read_only=True)
    seller_id = serializers.IntegerField(source='seller.id', read_only=True)
    seller_email = serializers.EmailField(source='seller.email', read_only=True)

    class Meta:
        model = OrderItem
        fields = (
            'id',
            'product_id',
            'seller_id',
            'seller_email',
            'product_title',
            'unit',
            'unit_price',
            'quantity',
            'line_total',
            'status',
            'allocated_at',
            'fulfilled_at',
            'cancelled_at',
        )


class OrderSerializer(serializers.ModelSerializer):
    """Output serializer for order aggregate details."""

    buyer_id = serializers.IntegerField(source='buyer.id', read_only=True)
    buyer_email = serializers.EmailField(source='buyer.email', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            'id',
            'order_number',
            'buyer_id',
            'buyer_email',
            'status',
            'currency',
            'subtotal_amount',
            'seller_count',
            'item_count',
            'notes',
            'placed_at',
            'confirmed_at',
            'cancelled_at',
            'completed_at',
            'cancellation_reason',
            'items',
        )
