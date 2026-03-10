"""Product listing statuses used by marketplace workflows."""

from django.db.models import TextChoices


class ListingStatus(TextChoices):
    """Lifecycle status options for marketplace products."""

    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'
    SOLD_OUT = 'sold_out', 'Sold Out'
    EXPIRED = 'expired', 'Expired'
