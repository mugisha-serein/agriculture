"""Serializers for discovery search API."""

from rest_framework import serializers

from discovery.domain.sorting import DiscoverySort


class DiscoverySearchSerializer(serializers.Serializer):
    """Input serializer for discovery search query params."""

    query = serializers.CharField(required=False, allow_blank=True)
    crop_id = serializers.IntegerField(required=False)
    min_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    max_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    radius_km = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    sort = serializers.ChoiceField(choices=DiscoverySort.choices, default=DiscoverySort.RELEVANCE)
    page = serializers.IntegerField(min_value=1, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, default=20)

    def validate(self, attrs):
        """Validate coordinate filters and price range relationships."""
        has_latitude = 'latitude' in attrs
        has_longitude = 'longitude' in attrs
        if has_latitude != has_longitude:
            raise serializers.ValidationError('Latitude and longitude must be provided together.')
        if 'radius_km' in attrs and not (has_latitude and has_longitude):
            raise serializers.ValidationError('Radius filter requires latitude and longitude.')
        min_price = attrs.get('min_price')
        max_price = attrs.get('max_price')
        if min_price is not None and max_price is not None and min_price > max_price:
            raise serializers.ValidationError('Minimum price cannot exceed maximum price.')
        return attrs


class DiscoveryProductSerializer(serializers.Serializer):
    """Output serializer for ranked discovery product rows."""

    id = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField()
    crop_id = serializers.IntegerField()
    crop_name = serializers.CharField()
    seller_id = serializers.IntegerField()
    seller_email = serializers.EmailField()
    unit = serializers.CharField()
    price_per_unit = serializers.DecimalField(max_digits=12, decimal_places=2)
    quantity_available = serializers.DecimalField(max_digits=12, decimal_places=3)
    minimum_order_quantity = serializers.DecimalField(max_digits=12, decimal_places=3)
    location_name = serializers.CharField()
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, allow_null=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, allow_null=True)
    expires_at = serializers.DateTimeField()
    score = serializers.FloatField()
    distance_km = serializers.FloatField(allow_null=True)

class PlatformSystemSerializer(serializers.Serializer):
    """Output serializer for platform systems."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    icon = serializers.CharField()
    target_url = serializers.CharField()
    position = serializers.IntegerField()
