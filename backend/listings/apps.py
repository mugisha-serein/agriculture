from django.apps import AppConfig


class ListingsConfig(AppConfig):
    """Configuration for the marketplace listings app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'listings'
    verbose_name = 'Marketplace'
