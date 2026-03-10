"""User role choices for identity and authorization boundaries."""

from django.db.models import TextChoices


class UserRole(TextChoices):
    """Role choices supported by the identity domain."""

    BUYER = 'buyer', 'Buyer'
    SELLER = 'seller', 'Seller'
    TRANSPORTER = 'transporter', 'Transporter'
    ADMIN = 'admin', 'Admin'
