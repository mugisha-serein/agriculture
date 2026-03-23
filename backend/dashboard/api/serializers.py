from rest_framework import serializers

class DashboardStatsSerializer(serializers.Serializer):
    """Aggregate statistics for the dashboard."""

    total_products = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    total_crops = serializers.IntegerField()
    total_shipments = serializers.IntegerField()
    total_reputation = serializers.FloatField()


class DashboardActivitySerializer(serializers.Serializer):
    """Individual activity record for dashboard feed."""

    type = serializers.CharField()  # sale, stock_low, out_of_stock, transaction
    description = serializers.CharField()
    timestamp = serializers.DateTimeField()
    metadata = serializers.JSONField(required=False)


class DashboardChartItemSerializer(serializers.Serializer):
    """Data point for usage chart."""

    name = serializers.CharField()
    value = serializers.FloatField()


class DashboardResponseSerializer(serializers.Serializer):
    """Full dashboard data payload."""

    stats = DashboardStatsSerializer()
    chart_data = DashboardChartItemSerializer(many=True)
    activity = DashboardActivitySerializer(many=True)


class MarketplaceHealthSerializer(serializers.Serializer):
    """Health metrics for the marketplace."""

    gmv = serializers.DecimalField(max_digits=16, decimal_places=2)
    active_sellers = serializers.IntegerField()
    conversion_rate = serializers.DecimalField(max_digits=5, decimal_places=4)
    cart_abandonment_rate = serializers.DecimalField(max_digits=5, decimal_places=4)
    delivery_success_rate = serializers.DecimalField(max_digits=5, decimal_places=4)
    gmv_growth = serializers.DecimalField(max_digits=5, decimal_places=4)


class AdminPanelSectionSerializer(serializers.Serializer):
    """Generic admin dashboard section payload."""

    title = serializers.CharField()
    summary = serializers.DictField(child=serializers.CharField(), required=False)
    metrics = serializers.ListField(child=serializers.DictField(), required=False)


class AdminPanelsSerializer(serializers.Serializer):
    """Grouped admin dashboards for compliance, fraud, and operations."""

    fraud_detection = AdminPanelSectionSerializer()
    verification_queue = AdminPanelSectionSerializer()
    payment_reconciliation = AdminPanelSectionSerializer()
    shipment_delays = AdminPanelSectionSerializer()
    seller_performance = AdminPanelSectionSerializer()


class AnalyticsResponseSerializer(serializers.Serializer):
    """Payload for the analytics engine overview."""

    marketplace_health = MarketplaceHealthSerializer()
    admin_panels = AdminPanelsSerializer()
