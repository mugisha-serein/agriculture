from django.db.models import Count, Sum, Q
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from dashboard.api.serializers import DashboardResponseSerializer
from listings.models import Product, Crop
from orders.models import Order, OrderItem
from logistics.models import Shipment
from payments.models import Payment
from reputation.services.reputation_service import ReputationService


class DashboardView(APIView):
    """Aggregate analytics and activity for sellers and transporters."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Return dashboard metrics filtered by year/month."""
        user = request.user
        year = request.query_params.get('year')
        month = request.query_params.get('month')

        # Base filters for the selected period
        period_filter = Q()
        if year:
            period_filter &= Q(created_at__year=year)
        if month:
            period_filter &= Q(created_at__month=month)

        if user.role == 'seller':
            data = self._get_seller_data(user, period_filter)
        elif user.role == 'transporter':
            data = self._get_transporter_data(user, period_filter)
        else:
            return Response({'detail': 'Dashboard not available for this role.'}, status=403)

        return Response(data, status=status.HTTP_200_OK)

    def _get_seller_data(self, user, period_filter):
        # Stats
        total_products = Product.objects.filter(seller=user, is_deleted=False).count()
        total_orders = OrderItem.objects.filter(seller=user).filter(period_filter).values('order').distinct().count()
        total_crops = Product.objects.filter(seller=user, is_deleted=False).values('crop').distinct().count()
        total_shipments = Shipment.objects.filter(seller=user).filter(period_filter).count()
        
        reputation_service = ReputationService()
        rep_summary = reputation_service.get_reputation_summary(user_id=user.id)
        total_reputation = rep_summary.get('bayesian_score', 0.0)

        # Chart Data (Top 5 products by sales volume in period)
        chart_data = (
            OrderItem.objects.filter(seller=user)
            .filter(period_filter)
            .values('product_title')
            .annotate(value=Sum('quantity'))
            .order_by('-value')[:5]
        )
        chart_data = [{'name': item['product_title'], 'value': float(item['value'])} for item in chart_data]

        # Activity
        activity = []
        
        # Sales
        recent_sales = OrderItem.objects.filter(seller=user).filter(period_filter).select_related('order').order_by('-created_at')[:5]
        for sale in recent_sales:
            activity.append({
                'type': 'sale',
                'description': f"Sold {sale.quantity}{sale.unit} of {sale.product_title} (Order #{sale.order.order_number})",
                'timestamp': sale.created_at
            })

        # Stock Alerts
        low_stock = Product.objects.filter(
            seller=user,
            is_deleted=False,
            inventory__available_quantity__gt=0,
            inventory__available_quantity__lt=10,
        ).select_related('inventory')[:3]
        for p in low_stock:
            available_qty = p.inventory.available_quantity if p.inventory else 0
            activity.append({
                'type': 'stock_low',
                'description': f"Low stock: {p.title} ({available_qty} left)",
                'timestamp': timezone.now() # Recent alert
            })
            
        out_of_stock = Product.objects.filter(
            seller=user,
            is_deleted=False,
            inventory__available_quantity=0,
        ).select_related('inventory')[:3]
        for p in out_of_stock:
            activity.append({
                'type': 'out_of_stock',
                'description': f"Out of stock: {p.title}",
                'timestamp': timezone.now()
            })

        # Transactions
        recent_payments = Payment.objects.filter(order__items__seller=user).filter(period_filter).distinct().order_by('-initiated_at')[:5]
        for p in recent_payments:
            activity.append({
                'type': 'transaction',
                'description': f"Payment {p.status}: {p.amount} {p.currency} (Ref: {p.payment_reference})",
                'timestamp': p.initiated_at
            })

        # Sort combined activity
        activity.sort(key=lambda x: x['timestamp'], reverse=True)

        return {
            'stats': {
                'total_products': total_products,
                'total_orders': total_orders,
                'total_crops': total_crops,
                'total_shipments': total_shipments,
                'total_reputation': total_reputation
            },
            'chart_data': chart_data,
            'activity': activity[:15]
        }

    def _get_transporter_data(self, user, period_filter):
        # Transporters don't have products/crops
        total_shipments = Shipment.objects.filter(transporter=user).filter(period_filter).count()
        total_orders = Shipment.objects.filter(transporter=user).filter(period_filter).values('order').distinct().count()
        
        reputation_service = ReputationService()
        rep_summary = reputation_service.get_reputation_summary(user_id=user.id)
        score = rep_summary.get('bayesian_score', 0.0)
        
        # Calculate rank among other transporters
        leaderboard = reputation_service.leaderboard(role='transporter', limit=1000)
        rank = "N/A"
        total_peers = len(leaderboard)
        for i, entry in enumerate(leaderboard):
            if entry['user_id'] == user.id:
                rank = f"#{i+1}"
                break
        
        display_reputation = f"{score:.1f} ({rank})" if rank != "N/A" else f"{score:.1f}"

        # Activity
        activity = []
        recent_shipments = Shipment.objects.filter(transporter=user).filter(period_filter).order_by('-updated_at')[:10]
        for s in recent_shipments:
            activity.append({
                'type': 'shipment',
                'description': f"Shipment #{s.shipment_reference} status: {s.status}",
                'timestamp': s.updated_at
            })

        return {
            'stats': {
                'total_products': 0,
                'total_orders': total_orders,
                'total_crops': 0,
                'total_shipments': total_shipments,
                'total_reputation': display_reputation
            },
            'chart_data': [], # No product usage for transporters
            'activity': activity
        }
