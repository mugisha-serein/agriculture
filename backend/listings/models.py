"""Marketplace models for crops and product listings."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from listings.domain.statuses import ListingStatus
from listings.domain.units import ProductUnit


class TimestampedModel(models.Model):
    """Abstract model with standard audit timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Crop(TimestampedModel):
    """Crop category for grouping marketplace products."""

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'crops'
        ordering = ['name']

    def __str__(self):
        """Return a readable representation of a crop category."""
        return self.name


class Product(TimestampedModel):
    """Marketplace listing entity representing a seller product offer."""

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='marketplace_products',
    )
    crop = models.ForeignKey(Crop, on_delete=models.PROTECT, related_name='products')
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=16, choices=ProductUnit.choices)
    minimum_order_quantity = models.DecimalField(max_digits=12, decimal_places=3, default=1)
    location_name = models.CharField(max_length=120)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    available_from = models.DateField(default=timezone.localdate)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=16, choices=ListingStatus.choices, default=ListingStatus.ACTIVE)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'products'
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                condition=Q(minimum_order_quantity__gt=0),
                name='products_minimum_order_quantity_gt_zero',
            ),
        ]

    def clean(self):
        """Validate marketplace listing field relationships."""
        if (self.latitude is None) != (self.longitude is None):
            raise ValidationError('Latitude and longitude must be provided together.')
        if self.expires_at <= timezone.now():
            raise ValidationError('Listing expiration must be in the future.')

    def __str__(self):
        """Return a readable representation of a marketplace listing."""
        return f'{self.title}:{self.id}'

    def get_active_pricing(self, now=None):
        """Return the active pricing entry for this product."""
        now = now or timezone.now()
        pricing = getattr(self, 'pricing', None)
        if pricing is not None:
            entries = list(pricing.all())
            candidates = [
                entry
                for entry in entries
                if entry.valid_from <= now and (entry.valid_to is None or entry.valid_to >= now)
            ]
            if candidates:
                return sorted(candidates, key=lambda item: (item.valid_from, item.id), reverse=True)[0]
            return None
        return ProductPricing.get_active_pricing(product=self, now=now)


class ProductInventory(TimestampedModel):
    """Inventory quantities for a product listing."""

    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='inventory',
    )
    available_quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    reserved_quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)

    class Meta:
        db_table = 'product_inventory'
        ordering = ['-updated_at']
        constraints = [
            models.CheckConstraint(
                condition=Q(available_quantity__gte=0),
                name='product_inventory_available_gte_zero',
            ),
            models.CheckConstraint(
                condition=Q(reserved_quantity__gte=0),
                name='product_inventory_reserved_gte_zero',
            ),
        ]

    def __str__(self):
        """Return a readable representation of inventory details."""
        return f'{self.product_id}:{self.available_quantity}'


class ProductMedia(TimestampedModel):
    """Media assets associated with a product listing."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='media',
    )
    url = models.URLField()
    media_type = models.CharField(max_length=32)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'product_media'
        ordering = ['position', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'position'],
                name='product_media_unique_position',
            )
        ]

    def __str__(self):
        """Return a readable representation of the media item."""
        return f'{self.product_id}:{self.media_type}:{self.position}'


class ProductPricing(TimestampedModel):
    """Pricing history for a product listing."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='pricing',
    )
    currency = models.CharField(max_length=8, default='USD')
    price = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'product_pricing'
        ordering = ['-valid_from', '-id']
        constraints = [
            models.CheckConstraint(
                condition=Q(price__gt=0),
                name='product_pricing_price_gt_zero',
            ),
            models.CheckConstraint(
                condition=Q(discount__gte=0),
                name='product_pricing_discount_gte_zero',
            ),
        ]

    def __str__(self):
        """Return a readable representation of the pricing entry."""
        return f'{self.product_id}:{self.currency}:{self.price}'

    @staticmethod
    def get_active_pricing(*, product, now=None):
        """Return the active pricing entry for a product."""
        now = now or timezone.now()
        return (
            ProductPricing.objects.filter(product=product, valid_from__lte=now)
            .filter(Q(valid_to__isnull=True) | Q(valid_to__gte=now))
            .order_by('-valid_from', '-id')
            .first()
        )
