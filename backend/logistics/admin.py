"""Admin registrations for logistics models."""

from django.contrib import admin

from logistics.models import Shipment


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    """Admin configuration for shipment records."""

    list_display = (
        'id',
        'shipment_reference',
        'tracking_code',
        'order',
        'seller',
        'buyer',
        'transporter',
        'status',
        'created_at',
    )
    list_filter = ('status',)
    search_fields = ('shipment_reference', 'tracking_code', 'order__order_number')
    ordering = ('-created_at',)
