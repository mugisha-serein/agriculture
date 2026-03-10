"""Unit of measure options for marketplace products."""

from django.db.models import TextChoices


class ProductUnit(TextChoices):
    """Supported product units for listing inventory and pricing."""

    KILOGRAM = 'kg', 'Kilogram'
    TON = 'ton', 'Ton'
    BAG = 'bag', 'Bag'
    CRATE = 'crate', 'Crate'
