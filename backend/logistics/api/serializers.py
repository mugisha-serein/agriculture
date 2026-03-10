"""Serializers for logistics shipment APIs."""

from rest_framework import serializers

from logistics.domain.statuses import ShipmentStatus
from logistics.models import Shipment


class ShipmentCreateSerializer(serializers.Serializer):
    """Input serializer for shipment creation."""

    order_id = serializers.IntegerField()
    seller_id = serializers.IntegerField()
    pickup_address = serializers.CharField(max_length=255)
    delivery_address = serializers.CharField(max_length=255)
    scheduled_pickup_at = serializers.DateTimeField(required=False)


class ShipmentAssignSerializer(serializers.Serializer):
    """Input serializer for transporter assignment."""

    transporter_id = serializers.IntegerField()


class ShipmentStatusUpdateSerializer(serializers.Serializer):
    """Input serializer for shipment status transition."""

    status = serializers.ChoiceField(choices=ShipmentStatus.choices)
    location_note = serializers.CharField(max_length=255, required=False, allow_blank=True)
    delivery_proof = serializers.CharField(required=False, allow_blank=True)


class ShipmentCancelSerializer(serializers.Serializer):
    """Input serializer for shipment cancellation."""

    reason = serializers.CharField()


class ShipmentConfirmDeliverySerializer(serializers.Serializer):
    """Input serializer for delivery confirmation."""

    confirmation_note = serializers.CharField(required=False, allow_blank=True)


class ShipmentListQuerySerializer(serializers.Serializer):
    """Query serializer for shipment list filtering."""

    status = serializers.ChoiceField(choices=ShipmentStatus.choices, required=False)


class ShipmentSerializer(serializers.ModelSerializer):
    """Output serializer for shipment aggregate details."""

    order_id = serializers.IntegerField(source='order.id', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    seller_id = serializers.IntegerField(source='seller.id', read_only=True)
    seller_email = serializers.EmailField(source='seller.email', read_only=True)
    buyer_id = serializers.IntegerField(source='buyer.id', read_only=True)
    buyer_email = serializers.EmailField(source='buyer.email', read_only=True)
    transporter_id = serializers.IntegerField(source='transporter.id', read_only=True, allow_null=True)
    transporter_email = serializers.EmailField(
        source='transporter.email',
        read_only=True,
        allow_null=True,
    )
    delivered_by_id = serializers.IntegerField(source='delivered_by.id', read_only=True, allow_null=True)

    class Meta:
        model = Shipment
        fields = (
            'id',
            'shipment_reference',
            'tracking_code',
            'order_id',
            'order_number',
            'seller_id',
            'seller_email',
            'buyer_id',
            'buyer_email',
            'transporter_id',
            'transporter_email',
            'status',
            'pickup_address',
            'delivery_address',
            'scheduled_pickup_at',
            'assigned_at',
            'picked_up_at',
            'in_transit_at',
            'delivered_at',
            'cancelled_at',
            'delivery_confirmed_at',
            'delivered_by_id',
            'last_location_note',
            'delivery_proof',
            'delivery_confirmation_note',
            'cancellation_reason',
            'created_at',
            'updated_at',
        )
