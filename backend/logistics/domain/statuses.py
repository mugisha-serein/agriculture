"""Shipment lifecycle status definitions."""

from django.db.models import TextChoices


class ShipmentStatus(TextChoices):
    """Lifecycle states for shipment coordination."""

    CREATED = 'created', 'Created'
    ASSIGNED = 'assigned', 'Assigned'
    PICKED_UP = 'picked_up', 'Picked Up'
    IN_TRANSIT = 'in_transit', 'In Transit'
    OUT_FOR_DELIVERY = 'out_for_delivery', 'Out for Delivery'
    DELIVERED = 'delivered', 'Delivered'
    FAILED = 'failed', 'Failed'
    RETURNED = 'returned', 'Returned'
    CANCELLED = 'cancelled', 'Cancelled'
