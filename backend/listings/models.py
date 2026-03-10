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
    price_per_unit = models.DecimalField(max_digits=12, decimal_places=2)
    quantity_available = models.DecimalField(max_digits=12, decimal_places=3)
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
                condition=Q(price_per_unit__gt=0),
                name='products_price_per_unit_gt_zero',
            ),
            models.CheckConstraint(
                condition=Q(quantity_available__gte=0),
                name='products_quantity_available_gte_zero',
            ),
            models.CheckConstraint(
                condition=Q(minimum_order_quantity__gt=0),
                name='products_minimum_order_quantity_gt_zero',
            ),
        ]

    def clean(self):
        """Validate marketplace listing field relationships."""
        if (self.latitude is None) != (self.longitude is None):
            raise ValidationError('Latitude and longitude must be provided together.')
        if self.minimum_order_quantity > self.quantity_available and self.quantity_available > 0:
            raise ValidationError('Minimum order quantity cannot exceed available quantity.')
        if self.expires_at <= timezone.now():
            raise ValidationError('Listing expiration must be in the future.')

    def __str__(self):
        """Return a readable representation of a marketplace listing."""
        return f'{self.title}:{self.id}'
