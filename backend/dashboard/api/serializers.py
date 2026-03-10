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
