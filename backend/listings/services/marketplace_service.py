"""Marketplace workflows for crops and listing lifecycle management."""

from decimal import Decimal
import math

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from listings.domain.statuses import ListingStatus
from listings.models import Crop, Product


class MarketplaceService:
    """Application service for marketplace domain operations."""

    def list_crops(self):
        """Return active crop categories."""
        return Crop.objects.filter(is_active=True).order_by('name')

    def create_crop(self, *, actor, name, description=''):
        """Create a crop category as a seller."""
        self._assert_seller(actor)
        slug = self._unique_slug_for_name(name)
        return Crop.objects.create(name=name.strip(), slug=slug, description=description)

    def update_crop(self, *, actor, crop_id, **changes):
        """Update a crop category as a seller."""
        self._assert_seller(actor)
        crop = self._get_crop(crop_id)
        
        mutable_fields = {'name', 'description', 'is_active'}
        for field_name, value in changes.items():
            if field_name not in mutable_fields:
                continue
            if field_name == 'name':
                crop.name = value.strip()
                crop.slug = self._unique_slug_for_name(value)
            else:
                setattr(crop, field_name, value)
        
        crop.save()
        return crop

    def delete_crop(self, *, actor, crop_id):
        """Soft-delete (deactivate) a crop category as a seller."""
        self._assert_seller(actor)
        crop = self._get_crop(crop_id)
        crop.is_active = False
        crop.save(update_fields=['is_active', 'updated_at'])

    @transaction.atomic
    def create_product(
        self,
        *,
        actor,
        crop_id,
        title,
        description='',
        unit,
        price_per_unit,
        quantity_available,
        minimum_order_quantity,
        location_name,
        latitude=None,
        longitude=None,
        available_from=None,
        expires_at,
        status=ListingStatus.ACTIVE,
    ):
        """Create a new marketplace listing as a seller."""
        self._assert_seller(actor)
        crop = self._get_crop(crop_id)
        self._validate_coordinates(latitude=latitude, longitude=longitude)
        self._validate_expiry(expires_at=expires_at)
        if Decimal(str(quantity_available)) <= 0:
            raise ValidationError({'quantity_available': ['Quantity must be greater than zero.']})
        if Decimal(str(minimum_order_quantity)) > Decimal(str(quantity_available)):
            raise ValidationError(
                {'minimum_order_quantity': ['Minimum order quantity cannot exceed quantity available.']}
            )

        if status not in {ListingStatus.ACTIVE, ListingStatus.INACTIVE}:
            status = ListingStatus.ACTIVE

        return Product.objects.create(
            seller=actor,
            crop=crop,
            title=title,
            description=description,
            unit=unit,
            price_per_unit=price_per_unit,
            quantity_available=quantity_available,
            minimum_order_quantity=minimum_order_quantity,
            location_name=location_name,
            latitude=latitude,
            longitude=longitude,
            available_from=available_from or timezone.localdate(),
            expires_at=expires_at,
            status=status,
        )

    def list_available_products(
        self,
        *,
        crop_id=None,
        seller_id=None,
        search=None,
        latitude=None,
        longitude=None,
        radius_km=None,
    ):
        """Return available products after applying expiry and search filters."""
        self.expire_outdated_products()
        queryset = Product.objects.select_related('crop', 'seller').filter(
            is_deleted=False,
            status=ListingStatus.ACTIVE,
            quantity_available__gt=0,
            available_from__lte=timezone.localdate(),
        )
        if crop_id is not None:
            queryset = queryset.filter(crop_id=crop_id)
        if seller_id is not None:
            queryset = queryset.filter(seller_id=seller_id)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(crop__name__icontains=search)
                | Q(location_name__icontains=search)
            )

        if latitude is not None and longitude is not None and radius_km is not None:
            filtered_ids = []
            for product in queryset.exclude(latitude__isnull=True).exclude(longitude__isnull=True):
                distance = self._distance_km(
                    latitude=float(latitude),
                    longitude=float(longitude),
                    target_latitude=float(product.latitude),
                    target_longitude=float(product.longitude),
                )
                if distance <= float(radius_km):
                    filtered_ids.append(product.id)
            queryset = queryset.filter(id__in=filtered_ids)

        return queryset

    def list_my_products(self, *, actor, status=None):
        """Return products owned by the authenticated seller."""
        self._assert_seller(actor)
        self.expire_outdated_products()
        queryset = Product.objects.select_related('crop').filter(
            seller=actor,
            is_deleted=False,
        )
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_product(self, *, product_id):
        """Return a single non-deleted product by identifier."""
        self.expire_outdated_products()
        try:
            return Product.objects.select_related('crop', 'seller').get(
                id=product_id,
                is_deleted=False,
            )
        except Product.DoesNotExist as exc:
            raise NotFound('Product was not found.') from exc

    @transaction.atomic
    def update_product(self, *, actor, product_id, **changes):
        """Update a marketplace listing as owner."""
        product = self.get_product(product_id=product_id)
        self._assert_owner(actor=actor, product=product)

        mutable_fields = {
            'crop_id',
            'title',
            'description',
            'unit',
            'price_per_unit',
            'quantity_available',
            'minimum_order_quantity',
            'location_name',
            'latitude',
            'longitude',
            'available_from',
            'expires_at',
            'status',
        }
        for field_name, value in changes.items():
            if field_name not in mutable_fields:
                continue
            if field_name == 'crop_id':
                product.crop = self._get_crop(value)
            else:
                setattr(product, field_name, value)

        self._validate_coordinates(latitude=product.latitude, longitude=product.longitude)
        self._validate_expiry(expires_at=product.expires_at)

        if product.quantity_available <= 0:
            product.status = ListingStatus.SOLD_OUT
        elif product.status in {ListingStatus.SOLD_OUT, ListingStatus.EXPIRED}:
            product.status = ListingStatus.ACTIVE

        if product.minimum_order_quantity > product.quantity_available and product.quantity_available > 0:
            raise ValidationError(
                {'minimum_order_quantity': ['Minimum order quantity cannot exceed quantity available.']}
            )

        product.full_clean()
        product.save()
        return product

    @transaction.atomic
    def delete_product(self, *, actor, product_id):
        """Soft-delete a marketplace listing as owner."""
        product = self.get_product(product_id=product_id)
        self._assert_owner(actor=actor, product=product)
        product.is_deleted = True
        product.deleted_at = timezone.now()
        product.status = ListingStatus.INACTIVE
        product.save(update_fields=['is_deleted', 'deleted_at', 'status', 'updated_at'])

    def expire_outdated_products(self):
        """Mark active listings as expired once their expiry timestamp passes."""
        return Product.objects.filter(
            is_deleted=False,
            expires_at__lte=timezone.now(),
        ).exclude(status=ListingStatus.EXPIRED).update(status=ListingStatus.EXPIRED)

    def _assert_seller(self, actor):
        """Enforce seller role for marketplace operations."""
        if not actor.is_authenticated:
            raise PermissionDenied('Authentication is required.')
        if getattr(actor, 'role', None) != 'seller':
            raise PermissionDenied('Only sellers can perform this action.')

    def _assert_owner(self, *, actor, product):
        """Enforce owner authorization for listing mutation."""
        if actor.id != product.seller_id:
            raise PermissionDenied('Only the seller owner can modify this listing.')

    def _validate_coordinates(self, *, latitude, longitude):
        """Validate geolocation coordinates and pair presence."""
        if (latitude is None) != (longitude is None):
            raise ValidationError({'location': ['Latitude and longitude must be provided together.']})

    def _validate_expiry(self, *, expires_at):
        """Validate listing expiry in relation to current time."""
        if expires_at <= timezone.now():
            raise ValidationError({'expires_at': ['Listing expiration must be in the future.']})

    def _get_crop(self, crop_id):
        """Resolve crop category or raise a validation error."""
        try:
            return Crop.objects.get(id=crop_id, is_active=True)
        except Crop.DoesNotExist as exc:
            raise ValidationError({'crop_id': ['Crop category does not exist.']}) from exc

    def _unique_slug_for_name(self, name):
        """Generate a unique slug for a crop category name."""
        base_slug = slugify(name)[:120] or 'crop'
        candidate = base_slug
        index = 1
        while Crop.objects.filter(slug=candidate).exists():
            candidate = f'{base_slug}-{index}'
            index += 1
        return candidate

    def _distance_km(
        self,
        *,
        latitude,
        longitude,
        target_latitude,
        target_longitude,
    ):
        """Calculate great-circle distance between two coordinates in kilometers."""
        radius = 6371.0
        lat1 = math.radians(latitude)
        lon1 = math.radians(longitude)
        lat2 = math.radians(target_latitude)
        lon2 = math.radians(target_longitude)
        delta_lat = lat2 - lat1
        delta_lon = lon2 - lon1
        a_value = math.sin(delta_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(
            delta_lon / 2
        ) ** 2
        c_value = 2 * math.atan2(math.sqrt(a_value), math.sqrt(1 - a_value))
        return radius * c_value
