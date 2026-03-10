"""Sorting options for discovery search results."""

from django.db.models import TextChoices


class DiscoverySort(TextChoices):
    """Supported sort strategies for discovery."""

    RELEVANCE = 'relevance', 'Relevance'
    PRICE_ASC = 'price_asc', 'Price Low To High'
    PRICE_DESC = 'price_desc', 'Price High To Low'
    NEWEST = 'newest', 'Newest'
    DISTANCE = 'distance', 'Distance'
