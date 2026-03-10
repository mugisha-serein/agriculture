"""Admin registrations for marketplace models."""

from django.contrib import admin

from listings.models import Crop, Product


@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    """Admin configuration for crop categories."""

    list_display = ('id', 'name', 'slug', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')
    ordering = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin configuration for marketplace products."""

    list_display = (
        'id',
        'title',
        'seller',
        'crop',
        'price_per_unit',
        'quantity_available',
        'status',
        'expires_at',
        'is_deleted',
    )
    list_filter = ('status', 'unit', 'is_deleted', 'crop')
    search_fields = ('title', 'seller__email', 'crop__name', 'location_name')
    ordering = ('-created_at',)
