"""Order lifecycle statuses."""

from django.db.models import TextChoices


class OrderStatus(TextChoices):
    """Lifecycle states for order aggregates."""

    PENDING = 'pending', 'Pending'
    CONFIRMED = 'confirmed', 'Confirmed'
    CANCELLED = 'cancelled', 'Cancelled'
    COMPLETED = 'completed', 'Completed'


class OrderItemStatus(TextChoices):
    """Lifecycle states for individual order items."""

    ALLOCATED = 'allocated', 'Allocated'
    FULFILLED = 'fulfilled', 'Fulfilled'
    CANCELLED = 'cancelled', 'Cancelled'
