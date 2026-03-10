"""App configuration for discovery domain."""

from django.apps import AppConfig


class DiscoveryConfig(AppConfig):
    """Configuration for discovery app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'discovery'
    verbose_name = 'Discovery'
