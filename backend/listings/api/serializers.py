"""Serializers for marketplace API endpoints."""

from django.utils import timezone
from rest_framework import serializers

from listings.domain.statuses import ListingStatus
from listings.domain.units import ProductUnit
from listings.models import Crop, Product, ProductMedia, ProductPricing


class CropSerializer(serializers.ModelSerializer):
    """Output serializer for crop categories."""

    class Meta:
        model = Crop
        fields = ('id', 'name', 'slug', 'description')


class CropCreateSerializer(serializers.Serializer):
    """Input serializer for crop category creation."""

    name = serializers.CharField(max_length=120)
    description = serializers.CharField(required=False, allow_blank=True)


class CropUpdateSerializer(serializers.Serializer):
    """Input serializer for crop category updates."""

    name = serializers.CharField(max_length=120, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)


class ProductSerializer(serializers.ModelSerializer):
    """Output serializer for marketplace listings."""

    seller_id = serializers.IntegerField(source='seller.id', read_only=True)
    seller_email = serializers.EmailField(source='seller.email', read_only=True)
    crop_id = serializers.IntegerField(source='crop.id', read_only=True)
    crop_name = serializers.CharField(source='crop.name', read_only=True)
    available_quantity = serializers.SerializerMethodField()
    reserved_quantity = serializers.SerializerMethodField()
    media = serializers.SerializerMethodField()
    pricing = serializers.SerializerMethodField()

    def get_available_quantity(self, obj):
        """Return the available quantity from inventory when present."""
        inventory = getattr(obj, 'inventory', None)
        if inventory is None:
            return 0
        return inventory.available_quantity

    def get_reserved_quantity(self, obj):
        """Return the reserved quantity from inventory when present."""
        inventory = getattr(obj, 'inventory', None)
        if inventory is None:
            return 0
        return inventory.reserved_quantity

    def get_media(self, obj):
        """Return media assets for a listing."""
        media = getattr(obj, 'media', None)
        if media is None:
            media = obj.media.all()
        return ProductMediaSerializer(media, many=True).data

    def get_pricing(self, obj):
        """Return pricing entries for a listing."""
        pricing = getattr(obj, 'pricing', None)
        if pricing is None:
            pricing = obj.pricing.all()
        return ProductPricingSerializer(pricing, many=True).data

    class Meta:
        model = Product
        fields = (
            'id',
            'seller_id',
            'seller_email',
            'crop_id',
            'crop_name',
            'title',
            'description',
            'unit',
            'available_quantity',
            'reserved_quantity',
            'minimum_order_quantity',
            'location_name',
            'latitude',
            'longitude',
            'available_from',
            'expires_at',
            'status',
            'media',
            'pricing',
            'created_at',
            'updated_at',
        )


class ProductMediaSerializer(serializers.ModelSerializer):
    """Output serializer for product media."""

    class Meta:
        model = ProductMedia
        fields = ('id', 'url', 'media_type', 'position')


class ProductPricingSerializer(serializers.ModelSerializer):
    """Output serializer for product pricing entries."""

    class Meta:
        model = ProductPricing
        fields = ('id', 'currency', 'price', 'discount', 'valid_from', 'valid_to')


class ProductCreateSerializer(serializers.Serializer):
    """Input serializer for listing creation requests."""

    crop_id = serializers.IntegerField()
    title = serializers.CharField(max_length=160)
    description = serializers.CharField(required=False, allow_blank=True)
    unit = serializers.ChoiceField(choices=ProductUnit.choices)
    currency = serializers.CharField(max_length=8, default='USD')
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    discount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default='0')
    valid_from = serializers.DateTimeField(required=False)
    valid_to = serializers.DateTimeField(required=False, allow_null=True)
    available_quantity = serializers.DecimalField(max_digits=12, decimal_places=3)
    reserved_quantity = serializers.DecimalField(max_digits=12, decimal_places=3, required=False, default='0')
    minimum_order_quantity = serializers.DecimalField(max_digits=12, decimal_places=3, default='1')
    location_name = serializers.CharField(max_length=120)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    available_from = serializers.DateField(required=False)
    expires_at = serializers.DateTimeField()
    status = serializers.ChoiceField(
        choices=[ListingStatus.ACTIVE, ListingStatus.INACTIVE],
        default=ListingStatus.ACTIVE,
    )

    def validate(self, attrs):
        """Validate paired geolocation fields and expiry logic."""
        latitude = attrs.get('latitude')
        longitude = attrs.get('longitude')
        if (latitude is None) != (longitude is None):
            raise serializers.ValidationError('Latitude and longitude must be provided together.')
        if attrs['expires_at'] <= timezone.now():
            raise serializers.ValidationError('Listing expiration must be in the future.')
        if attrs.get('valid_to') and attrs.get('valid_from') and attrs['valid_to'] <= attrs['valid_from']:
            raise serializers.ValidationError('Pricing valid_to must be after valid_from.')
        return attrs


class ProductUpdateSerializer(serializers.Serializer):
    """Input serializer for partial listing updates."""

    crop_id = serializers.IntegerField(required=False)
    title = serializers.CharField(max_length=160, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    unit = serializers.ChoiceField(choices=ProductUnit.choices, required=False)
    currency = serializers.CharField(max_length=8, required=False)
    price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    discount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    valid_from = serializers.DateTimeField(required=False)
    valid_to = serializers.DateTimeField(required=False, allow_null=True)
    available_quantity = serializers.DecimalField(max_digits=12, decimal_places=3, required=False)
    reserved_quantity = serializers.DecimalField(max_digits=12, decimal_places=3, required=False)
    minimum_order_quantity = serializers.DecimalField(max_digits=12, decimal_places=3, required=False)
    location_name = serializers.CharField(max_length=120, required=False)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    available_from = serializers.DateField(required=False)
    expires_at = serializers.DateTimeField(required=False)
    status = serializers.ChoiceField(
        choices=[
            ListingStatus.ACTIVE,
            ListingStatus.INACTIVE,
            ListingStatus.SOLD_OUT,
            ListingStatus.EXPIRED,
        ],
        required=False,
    )


class MarketplaceQuerySerializer(serializers.Serializer):
    """Serializer for marketplace list query parameters."""

    crop_id = serializers.IntegerField(required=False)
    seller_id = serializers.IntegerField(required=False)
    search = serializers.CharField(required=False, allow_blank=True)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    radius_km = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
