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
        default=ShipmentStatus.CREATED,
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


class DeliveryPartner(TimestampedModel):
    """Third-party delivery partner profiles."""

    name = models.CharField(max_length=128)
    contact_name = models.CharField(max_length=128, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'delivery_partners'
        ordering = ['name']

    def __str__(self):
        return self.name


class DeliveryRoute(TimestampedModel):
    """Planned delivery route assigned to a vehicle."""

    route_code = models.CharField(max_length=32, unique=True)
    delivery_partner = models.ForeignKey(
        DeliveryPartner,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='routes',
    )
    vehicle_identifier = models.CharField(max_length=64)
    driver_name = models.CharField(max_length=128)
    capacity = models.PositiveIntegerField(default=4)
    status = models.CharField(max_length=32, default='planned')
    estimated_start = models.DateTimeField(null=True, blank=True)
    estimated_end = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'delivery_routes'

    @staticmethod
    def generate_route_code():
        """Generate a short route code."""
        return f'RTE-{timezone.now().strftime("%Y%m%d")}-{uuid4().hex[:6].upper()}'

    def __str__(self):
        return self.route_code


class ShipmentItem(TimestampedModel):
    """Route assignment for a shipment."""

    route = models.ForeignKey(
        DeliveryRoute,
        on_delete=models.CASCADE,
        related_name='shipment_items',
    )
    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.PROTECT,
        related_name='route_items',
    )
    sequence = models.PositiveIntegerField(default=0)
    planned_arrival = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=24,
        choices=ShipmentStatus.choices,
        default=ShipmentStatus.ASSIGNED,
    )

    class Meta:
        db_table = 'shipment_items'
        unique_together = ('route', 'shipment')
        ordering = ['route', 'sequence']

    def __str__(self):
        return f'{self.route.route_code} - {self.shipment.shipment_reference}'


class ShipmentTrackingEvent(TimestampedModel):
    """GPS/telemetry events for a shipment."""

    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.CASCADE,
        related_name='tracking_events',
    )
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lng = models.DecimalField(max_digits=9, decimal_places=6)
    status = models.CharField(
        max_length=24,
        choices=ShipmentStatus.choices,
    )
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'shipment_tracking_events'
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.shipment.shipment_reference} @ {self.timestamp:%Y-%m-%d %H:%M}'
