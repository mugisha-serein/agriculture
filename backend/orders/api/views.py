"""API views for order lifecycle operations."""

from rest_framework import permissions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.api.serializers import OrderCancelSerializer
from orders.api.serializers import OrderCreateSerializer
from orders.api.serializers import OrderListQuerySerializer
from orders.api.serializers import OrderSerializer
from orders.services.order_service import OrderService


class OrderListCreateView(APIView):
    """Create buyer orders and list buyer-owned orders."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """List orders for the authenticated buyer."""
        query_serializer = OrderListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        service = OrderService()
        orders = service.list_buyer_orders(actor=request.user, **query_serializer.validated_data)
        return Response(OrderSerializer(orders, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new order from provided product items."""
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = OrderService()
        order = service.create_order(actor=request.user, **serializer.validated_data)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class SellerOrderListView(APIView):
    """List seller-participating orders for the authenticated seller."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """List orders where the authenticated user is a seller participant."""
        query_serializer = OrderListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        service = OrderService()
        orders = service.list_seller_orders(actor=request.user, **query_serializer.validated_data)
        return Response(OrderSerializer(orders, many=True).data, status=status.HTTP_200_OK)


class OrderDetailView(APIView):
    """Retrieve a single order by identifier."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_id):
        """Return order details for authorized participants."""
        service = OrderService()
        order = service.get_order(actor=request.user, order_id=order_id)
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)


class OrderConfirmView(APIView):
    """Confirm pending orders."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id):
        """Confirm an order as buyer owner or admin."""
        service = OrderService()
        order = service.confirm_order(actor=request.user, order_id=order_id)
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)


class OrderCancelView(APIView):
    """Cancel pending or confirmed orders according to policy."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id):
        """Cancel an order and restore allocated inventory."""
        serializer = OrderCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = OrderService()
        order = service.cancel_order(
            actor=request.user,
            order_id=order_id,
            reason=serializer.validated_data['reason'],
        )
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)


class OrderFulfillItemView(APIView):
    """Fulfill individual order items as seller owner or admin."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id, item_id):
        """Mark one order item fulfilled and complete order when all items are fulfilled."""
        service = OrderService()
        order = service.fulfill_order_item(actor=request.user, order_id=order_id, item_id=item_id)
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)
