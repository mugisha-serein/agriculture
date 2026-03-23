from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from listings.models import Product
from orders.models import Order


class TimestampedModel(models.Model):
    """Abstract base model with audit-friendly timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class DailySalesMetric(TimestampedModel):
    """Daily rollup of marketplace revenue and funnel health."""

    date = models.DateField(unique=True)
    gmv = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'))
    orders_count = models.PositiveIntegerField(default=0)
    active_sellers = models.PositiveIntegerField(default=0)
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    cart_abandonment_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    delivery_success_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0)

    class Meta:
        db_table = 'daily_sales_metrics'
        ordering = ['-date']

    def __str__(self):
        return f'DailySalesMetric {self.date.isoformat()}'


class ProductPerformance(TimestampedModel):
    """Per-product performance snapshots for the data warehouse."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='performances')
    date = models.DateField()
    units_sold = models.DecimalField(max_digits=14, decimal_places=3, default=Decimal('0.000'))
    revenue = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'))
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    cart_abandonment_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'product_performance'
        ordering = ['-date']
        unique_together = [['product', 'date']]

    def __str__(self):
        return f'{self.product_id} @ {self.date:%Y-%m-%d}'


class SellerPerformance(TimestampedModel):
    """Seller performance metrics per day."""

    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='performance_records')
    date = models.DateField()
    gmv = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'))
    orders_count = models.PositiveIntegerField(default=0)
    delivery_success_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    fulfillment_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    rating_score = models.DecimalField(max_digits=5, decimal_places=4, default=0)

    class Meta:
        db_table = 'seller_performance'
        ordering = ['-date']
        unique_together = [['seller', 'date']]

    def __str__(self):
        return f'{self.seller_id} performance @ {self.date}'


class BuyerActivity(TimestampedModel):
    """Buyer-centric activity summarizing engagement and abandonment."""

    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activity_records')
    date = models.DateField()
    orders_count = models.PositiveIntegerField(default=0)
    total_spend = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'))
    average_cart_value = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'))
    cart_abandonment_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    last_active_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'buyer_activity'
        ordering = ['-date']
        unique_together = [['buyer', 'date']]

    def __str__(self):
        return f'{self.buyer_id} buyer activity @ {self.date}'
