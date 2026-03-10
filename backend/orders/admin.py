"""Admin registrations for orders models."""

from django.contrib import admin

from orders.models import Order
from orders.models import OrderItem


class OrderItemInline(admin.TabularInline):
    """Inline display for order items within order admin."""

    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'seller', 'product_title', 'unit_price', 'quantity', 'line_total')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin configuration for order aggregate records."""

    list_display = (
        'id',
        'order_number',
        'buyer',
        'status',
        'subtotal_amount',
        'seller_count',
        'item_count',
        'placed_at',
    )
    list_filter = ('status',)
    search_fields = ('order_number', 'buyer__email')
    ordering = ('-placed_at',)
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Admin configuration for order line items."""

    list_display = (
        'id',
        'order',
        'product',
        'seller',
        'unit_price',
        'quantity',
        'line_total',
        'status',
    )
    list_filter = ('status',)
    search_fields = ('order__order_number', 'seller__email', 'product_title')
    ordering = ('order_id', 'id')
