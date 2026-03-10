"""Logistics models for shipment coordination and tracking."""

from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils import timezone

from logistics.domain.statuses import ShipmentStatus


class TimestampedModel(models.Model):
    """Abstract model with audit timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Shipment(TimestampedModel):
    """Shipment aggregate for order-level coordination and tracking."""

    shipment_reference = models.CharField(max_length=40, unique=True)
    tracking_code = models.CharField(max_length=40, unique=True)
    order = models.ForeignKey('orders.Order', on_delete=models.PROTECT, related_name='shipments')
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='seller_shipments',
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='buyer_shipments',
    )
    transporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='transporter_shipments',
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=24,
        choices=ShipmentStatus.choices,
        default=ShipmentStatus.PENDING_ASSIGNMENT,
    )
    pickup_address = models.CharField(max_length=255)
    delivery_address = models.CharField(max_length=255)
    scheduled_pickup_at = models.DateTimeField(null=True, blank=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    in_transit_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    delivery_confirmed_at = models.DateTimeField(null=True, blank=True)
    delivered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='delivered_shipments',
        null=True,
        blank=True,
    )
    last_location_note = models.CharField(max_length=255, blank=True)
    delivery_proof = models.TextField(blank=True)
    delivery_confirmation_note = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_shipments',
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'shipments'
        ordering = ['-created_at']

    def __str__(self):
        """Return readable shipment reference."""
        return self.shipment_reference

    @staticmethod
    def generate_shipment_reference():
        """Generate a unique shipment reference identifier."""
        return f'SHP-{timezone.now().strftime("%Y%m%d")}-{uuid4().hex[:10].upper()}'

    @staticmethod
    def generate_tracking_code():
        """Generate a unique tracking code identifier."""
        return f'TRK-{uuid4().hex[:12].upper()}'
