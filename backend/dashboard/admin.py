from django.contrib import admin

from dashboard.models import BuyerActivity
from dashboard.models import DailySalesMetric
from dashboard.models import ProductPerformance
from dashboard.models import SellerPerformance


@admin.register(DailySalesMetric)
class DailySalesMetricAdmin(admin.ModelAdmin):
    list_display = ('date', 'gmv', 'orders_count', 'active_sellers')
    ordering = ('-date',)


@admin.register(ProductPerformance)
class ProductPerformanceAdmin(admin.ModelAdmin):
    list_display = ('product', 'date', 'units_sold', 'revenue')
    list_filter = ('date',)
    ordering = ('-date',)


@admin.register(SellerPerformance)
class SellerPerformanceAdmin(admin.ModelAdmin):
    list_display = ('seller', 'date', 'gmv', 'delivery_success_rate')
    list_filter = ('date',)
    ordering = ('-date',)


@admin.register(BuyerActivity)
class BuyerActivityAdmin(admin.ModelAdmin):
    list_display = ('buyer', 'date', 'orders_count', 'total_spend')
    list_filter = ('date',)
    ordering = ('-date',)
