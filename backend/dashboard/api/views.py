"""Dashboard APIs powering seller/transporter widgets and admin analytics."""

from datetime import timedelta
from decimal import Decimal

from django.db.models import Q, Sum
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from audit.domain.alerts import AlertSeverity
from audit.models import AuditAlert
from dashboard.api.serializers import AnalyticsResponseSerializer
from dashboard.api.serializers import DashboardResponseSerializer
from dashboard.models import DailySalesMetric
from dashboard.models import SellerPerformance
from listings.domain.statuses import ListingStatus
from listings.models import Product
from orders.domain.statuses import OrderStatus
from orders.models import Order, OrderItem
from logistics.domain.statuses import ShipmentStatus
from logistics.models import Shipment
from payments.domain.statuses import PaymentStatus
from payments.models import Payment
from reputation.services.reputation_service import ReputationService
from verification.domain.statuses import VerificationStatus
from verification.models import UserVerification


class DashboardView(APIView):
    """Aggregate analytics and activity for sellers and transporters."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Return dashboard metrics filtered by year/month."""
        user = request.user
        year = request.query_params.get('year')
        month = request.query_params.get('month')

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
        total_products = Product.objects.filter(seller=user, is_deleted=False).count()
        total_orders = (
            OrderItem.objects.filter(seller=user)
            .filter(period_filter)
            .values('order')
            .distinct()
            .count()
        )
        total_crops = (
            Product.objects.filter(seller=user, is_deleted=False).values('crop').distinct().count()
        )
        total_shipments = Shipment.objects.filter(seller=user).filter(period_filter).count()

        reputation_service = ReputationService()
        rep_summary = reputation_service.get_reputation_summary(user_id=user.id)
        total_reputation = rep_summary.get('bayesian_score', 0.0)

        chart_data = (
            OrderItem.objects.filter(seller=user)
            .filter(period_filter)
            .values('product_title')
            .annotate(value=Sum('quantity'))
            .order_by('-value')[:5]
        )
        chart_data = [{'name': item['product_title'], 'value': float(item['value'])} for item in chart_data]

        activity = []
        recent_sales = (
            OrderItem.objects.filter(seller=user)
            .filter(period_filter)
            .select_related('order')
            .order_by('-created_at')[:5]
        )
        for sale in recent_sales:
            activity.append(
                {
                    'type': 'sale',
                    'description': f"Sold {sale.quantity}{sale.unit} of {sale.product_title} (Order #{sale.order.order_number})",
                    'timestamp': sale.created_at,
                    'metadata': {'order_id': sale.order_id},
                }
            )

        low_stock = (
            Product.objects.filter(
                seller=user,
                is_deleted=False,
                inventory__available_quantity__gt=0,
                inventory__available_quantity__lt=10,
            )
            .select_related('inventory')[:3]
        )
        for p in low_stock:
            available_qty = p.inventory.available_quantity if p.inventory else Decimal('0.00')
            activity.append(
                {
                    'type': 'stock_low',
                    'description': f"Low stock: {p.title} ({available_qty} left)",
                    'timestamp': timezone.now(),
                    'metadata': {'product_id': p.id},
                }
            )

        out_of_stock = (
            Product.objects.filter(
                seller=user,
                is_deleted=False,
                inventory__available_quantity=0,
            )
            .select_related('inventory')[:3]
        )
        for p in out_of_stock:
            activity.append(
                {
                    'type': 'out_of_stock',
                    'description': f"Out of stock: {p.title}",
                    'timestamp': timezone.now(),
                    'metadata': {'product_id': p.id},
                }
            )

        recent_payments = (
            Payment.objects.filter(order__items__seller=user)
            .filter(period_filter)
            .distinct()
            .order_by('-initiated_at')[:5]
        )
        for p in recent_payments:
            activity.append(
                {
                    'type': 'transaction',
                    'description': f"Payment {p.status}: {p.amount} {p.currency} (Ref: {p.payment_reference})",
                    'timestamp': p.initiated_at,
                    'metadata': {'payment_id': p.id},
                }
            )

        activity.sort(key=lambda x: x['timestamp'], reverse=True)

        return {
            'stats': {
                'total_products': total_products,
                'total_orders': total_orders,
                'total_crops': total_crops,
                'total_shipments': total_shipments,
                'total_reputation': total_reputation,
            },
            'chart_data': chart_data,
            'activity': activity[:15],
        }

    def _get_transporter_data(self, user, period_filter):
        total_shipments = Shipment.objects.filter(transporter=user).filter(period_filter).count()
        total_orders = (
            Shipment.objects.filter(transporter=user)
            .filter(period_filter)
            .values('order')
            .distinct()
            .count()
        )

        reputation_service = ReputationService()
        rep_summary = reputation_service.get_reputation_summary(user_id=user.id)
        score = rep_summary.get('bayesian_score', 0.0)

        leaderboard = reputation_service.leaderboard(role='transporter', limit=1000)
        rank = 'N/A'
        for idx, entry in enumerate(leaderboard, start=1):
            if entry['user_id'] == user.id:
                rank = f'#{idx}'
                break

        display_reputation = f"{score:.1f} ({rank})" if rank != 'N/A' else f"{score:.1f}"

        activity = []
        recent_shipments = (
            Shipment.objects.filter(transporter=user)
            .filter(period_filter)
            .order_by('-updated_at')[:10]
        )
        for s in recent_shipments:
            activity.append(
                {
                    'type': 'shipment',
                    'description': f"Shipment #{s.shipment_reference} status: {s.status}",
                    'timestamp': s.updated_at,
                }
            )

        return {
            'stats': {
                'total_products': 0,
                'total_orders': total_orders,
                'total_crops': 0,
                'total_shipments': total_shipments,
                'total_reputation': display_reputation,
            },
            'chart_data': [],
            'activity': activity,
        }


class AnalyticsOverviewView(APIView):
    """Admin-only analytics engine delivering marketplace health and panels."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if not self._is_admin(user):
            return Response({'detail': 'Analytics dashboards are admin only.'}, status=status.HTTP_403_FORBIDDEN)

        payload = {
            'marketplace_health': self._marketplace_health(),
            'admin_panels': self._admin_panels(),
        }
        serializer = AnalyticsResponseSerializer(payload)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _is_admin(self, user):
        return bool(user.is_authenticated and (user.is_staff or user.role == 'admin'))

    def _marketplace_health(self):
        metric = DailySalesMetric.objects.order_by('-date').first()
        if metric:
            metric_data = {
                'gmv': metric.gmv,
                'active_sellers': metric.active_sellers,
                'conversion_rate': metric.conversion_rate,
                'cart_abandonment_rate': metric.cart_abandonment_rate,
                'delivery_success_rate': metric.delivery_success_rate,
                'gmv_growth': self._calc_growth(metric),
            }
            return metric_data
        return self._compute_live_marketplace_health()

    def _calc_growth(self, metric):
        previous = DailySalesMetric.objects.filter(date__lt=metric.date).order_by('-date').first()
        if previous and previous.gmv:
            return (metric.gmv - previous.gmv) / previous.gmv
        return Decimal('0.00')

    def _compute_live_marketplace_health(self):
        completed_orders = Order.objects.filter(status=OrderStatus.COMPLETED)
        completed_count = completed_orders.count()
        total_orders = Order.objects.count()
        gmv = completed_orders.aggregate(total=Sum('subtotal_amount'))['total'] or Decimal('0.00')
        conversion_rate = Decimal(completed_count) / Decimal(total_orders or 1)

        abandonment_window = timezone.now() - timedelta(hours=24)
        abandoned = Order.objects.filter(status=OrderStatus.PENDING, placed_at__lt=abandonment_window).count()
        cart_abandonment_rate = Decimal(abandoned) / Decimal(total_orders or 1)
        active_sellers = Product.objects.filter(is_deleted=False, status=ListingStatus.ACTIVE).values('seller').distinct().count()

        shipments = Shipment.objects.exclude(status=ShipmentStatus.CANCELLED)
        total_shipments = shipments.count()
        success = shipments.filter(status=ShipmentStatus.DELIVERED).count()
        delivery_success_rate = Decimal(success) / Decimal(total_shipments or 1)

        return {
            'gmv': gmv,
            'active_sellers': active_sellers,
            'conversion_rate': conversion_rate.quantize(Decimal('0.0001')),
            'cart_abandonment_rate': cart_abandonment_rate.quantize(Decimal('0.0001')),
            'delivery_success_rate': delivery_success_rate.quantize(Decimal('0.0001')),
            'gmv_growth': Decimal('0.00'),
        }

    def _admin_panels(self):
        return {
            'fraud_detection': self._fraud_detection_panel(),
            'verification_queue': self._verification_queue_panel(),
            'payment_reconciliation': self._payment_reconciliation_panel(),
            'shipment_delays': self._shipment_delays_panel(),
            'seller_performance': self._seller_performance_panel(),
        }

    def _fraud_detection_panel(self):
        window = timezone.now() - timedelta(days=7)
        recent_alerts = AuditAlert.objects.order_by('-triggered_at')[:5]
        alerts_past_week = AuditAlert.objects.filter(triggered_at__gte=window)
        summary = {
            'critical_alerts': str(alerts_past_week.filter(severity=AlertSeverity.CRITICAL).count()),
            'warning_alerts': str(alerts_past_week.filter(severity=AlertSeverity.WARNING).count()),
        }
        metrics = [
            {
                'alert_type': alert.alert_type,
                'severity': alert.severity,
                'description': alert.description,
                'triggered_at': alert.triggered_at.isoformat(),
            }
            for alert in recent_alerts
        ]
        return {'title': 'Fraud Detection', 'summary': summary, 'metrics': metrics}

    def _verification_queue_panel(self):
        pending = UserVerification.objects.filter(status=VerificationStatus.PENDING)
        pending_count = pending.count()
        oldest = pending.order_by('submitted_at').first()
        age_hours = (
            (timezone.now() - oldest.submitted_at).total_seconds() / 3600 if oldest else 0
        )
        summary = {
            'pending_verifications': str(pending_count),
            'oldest_queue_hours': f"{age_hours:.1f}",
        }
        return {'title': 'Verification Queue', 'summary': summary, 'metrics': []}

    def _payment_reconciliation_panel(self):
        failed = Payment.objects.filter(status=PaymentStatus.FAILED)
        refunded = Payment.objects.filter(status=PaymentStatus.REFUNDED)
        summary = {
            'failed_payments': str(failed.count()),
            'refunded_payments': str(refunded.count()),
            'refunded_volume': str(refunded.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')),
        }
        metrics = [
            {'status': 'failed', 'count': failed.count()},
            {'status': 'refunded', 'count': refunded.count()},
        ]
        return {'title': 'Payment Reconciliation', 'summary': summary, 'metrics': metrics}

    def _shipment_delays_panel(self):
        delay_threshold = timezone.now() - timedelta(hours=48)
        delayed_shipments = Shipment.objects.filter(
            scheduled_pickup_at__lt=delay_threshold,
            status__in=[
                ShipmentStatus.ASSIGNED,
                ShipmentStatus.PICKED_UP,
                ShipmentStatus.IN_TRANSIT,
                ShipmentStatus.OUT_FOR_DELIVERY,
            ],
        )
        count = delayed_shipments.count()
        summary = {
            'delayed_shipments': str(count),
            'average_delay_hours': f"{(count and 48) or 0}",
        }
        metrics = [
            {'shipment_reference': shipment.shipment_reference, 'status': shipment.status}
            for shipment in delayed_shipments[:5]
        ]
        return {'title': 'Shipment Delays', 'summary': summary, 'metrics': metrics}

    def _seller_performance_panel(self):
        recent = SellerPerformance.objects.order_by('-date')[:5]
        summary = {
            'tracked_sellers': str(recent.count()),
            'delivery_success_rate': str(
                recent.aggregate(avg=Sum('delivery_success_rate'))['avg'] if recent else Decimal('0.00')
            ),
        }
        metrics = [
            {
                'seller_id': record.seller_id,
                'gmv': str(record.gmv),
                'delivery_success_rate': str(record.delivery_success_rate),
                'rating_score': str(record.rating_score),
            }
            for record in recent
        ]
        return {'title': 'Seller Performance', 'summary': summary, 'metrics': metrics}
