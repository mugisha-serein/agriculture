"""Admin registrations for logistics models."""

from django.contrib import admin

from logistics.models import DeliveryPartner
from logistics.models import DeliveryRoute
from logistics.models import Shipment
from logistics.models import ShipmentItem
from logistics.models import ShipmentTrackingEvent


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


@admin.register(DeliveryPartner)
class DeliveryPartnerAdmin(admin.ModelAdmin):
    """Admin configuration for delivery partners."""

    list_display = ('id', 'name', 'contact_name', 'phone', 'is_active')
    search_fields = ('name', 'contact_name', 'email')
    ordering = ('name',)


@admin.register(DeliveryRoute)
class DeliveryRouteAdmin(admin.ModelAdmin):
    """Admin configuration for delivery routes."""

    list_display = ('id', 'route_code', 'vehicle_identifier', 'driver_name', 'status')
    search_fields = ('route_code', 'vehicle_identifier', 'driver_name')
    ordering = ('-created_at',)


@admin.register(ShipmentItem)
class ShipmentItemAdmin(admin.ModelAdmin):
    """Admin configuration for route shipment memberships."""

    list_display = ('id', 'route', 'shipment', 'sequence', 'status')
    search_fields = ('route__route_code', 'shipment__shipment_reference')
    ordering = ('route', 'sequence')


@admin.register(ShipmentTrackingEvent)
class ShipmentTrackingEventAdmin(admin.ModelAdmin):
    """Admin configuration for tracking telemetry."""

    list_display = ('id', 'shipment', 'status', 'timestamp', 'lat', 'lng')
    search_fields = ('shipment__shipment_reference',)
    ordering = ('-timestamp',)
