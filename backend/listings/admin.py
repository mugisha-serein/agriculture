"""Admin registrations for marketplace models."""

from django.contrib import admin

from listings.models import Crop, Product, ProductInventory, ProductMedia, ProductPricing


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
        'available_quantity',
        'status',
        'expires_at',
        'is_deleted',
    )
    list_filter = ('status', 'unit', 'is_deleted', 'crop')
    search_fields = ('title', 'seller__email', 'crop__name', 'location_name')
    ordering = ('-created_at',)

    @admin.display(description='available_quantity')
    def available_quantity(self, obj):
        """Return available quantity from inventory when present."""
        inventory = getattr(obj, 'inventory', None)
        if inventory is None:
            return None
        return inventory.available_quantity


@admin.register(ProductInventory)
class ProductInventoryAdmin(admin.ModelAdmin):
    """Admin configuration for product inventory records."""

    list_display = ('id', 'product', 'available_quantity', 'reserved_quantity', 'updated_at')
    list_filter = ('updated_at',)
    search_fields = ('product__title', 'product__seller__email')
    ordering = ('-updated_at',)


@admin.register(ProductMedia)
class ProductMediaAdmin(admin.ModelAdmin):
    """Admin configuration for product media."""

    list_display = ('id', 'product', 'media_type', 'position', 'created_at')
    list_filter = ('media_type',)
    search_fields = ('product__title',)
    ordering = ('product', 'position')


@admin.register(ProductPricing)
class ProductPricingAdmin(admin.ModelAdmin):
    """Admin configuration for product pricing."""

    list_display = ('id', 'product', 'currency', 'price', 'discount', 'valid_from', 'valid_to')
    list_filter = ('currency',)
    search_fields = ('product__title',)
    ordering = ('-valid_from',)
