"""Shipment lifecycle status definitions."""

from django.db.models import TextChoices


class ShipmentStatus(TextChoices):
    """Lifecycle states for shipment coordination."""

    PENDING_ASSIGNMENT = 'pending_assignment', 'Pending Assignment'
    ASSIGNED = 'assigned', 'Assigned'
    PICKED_UP = 'picked_up', 'Picked Up'
    IN_TRANSIT = 'in_transit', 'In Transit'
    DELIVERED = 'delivered', 'Delivered'
    CANCELLED = 'cancelled', 'Cancelled'
