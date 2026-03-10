"""API views for logistics shipment coordination."""

from rest_framework import permissions, status
from core.permissions import IsVerifiedRole
from rest_framework.response import Response
from rest_framework.views import APIView

from logistics.api.serializers import ShipmentAssignSerializer
from logistics.api.serializers import ShipmentCancelSerializer
from logistics.api.serializers import ShipmentConfirmDeliverySerializer
from logistics.api.serializers import ShipmentCreateSerializer
from logistics.api.serializers import ShipmentListQuerySerializer
from logistics.api.serializers import ShipmentSerializer
from logistics.api.serializers import ShipmentStatusUpdateSerializer
from logistics.services.logistics_service import LogisticsService


class ShipmentListCreateView(APIView):
    """Create shipments and list actor-visible shipments."""

    permission_classes = [permissions.IsAuthenticated, IsVerifiedRole]

    def get(self, request):
        """List shipments visible to authenticated actor."""
        query_serializer = ShipmentListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        service = LogisticsService()
        shipments = service.list_shipments(actor=request.user, **query_serializer.validated_data)
        return Response(ShipmentSerializer(shipments, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a shipment for order seller allocation."""
        serializer = ShipmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = LogisticsService()
        shipment = service.create_shipment(actor=request.user, **serializer.validated_data)
        return Response(ShipmentSerializer(shipment).data, status=status.HTTP_201_CREATED)


class ShipmentDetailView(APIView):
    """Retrieve shipment details."""

    permission_classes = [permissions.IsAuthenticated, IsVerifiedRole]

    def get(self, request, shipment_id):
        """Return shipment details for authorized actor."""
        service = LogisticsService()
        shipment = service.get_shipment(actor=request.user, shipment_id=shipment_id)
        return Response(ShipmentSerializer(shipment).data, status=status.HTTP_200_OK)


class ShipmentAssignView(APIView):
    """Assign transporter to shipment."""

    permission_classes = [permissions.IsAuthenticated, IsVerifiedRole]

    def post(self, request, shipment_id):
        """Assign transporter for shipment identifier."""
        serializer = ShipmentAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = LogisticsService()
        shipment = service.assign_transporter(
            actor=request.user,
            shipment_id=shipment_id,
            transporter_id=serializer.validated_data['transporter_id'],
        )
        return Response(ShipmentSerializer(shipment).data, status=status.HTTP_200_OK)


class ShipmentStatusUpdateView(APIView):
    """Update shipment tracking status."""

    permission_classes = [permissions.IsAuthenticated, IsVerifiedRole]

    def post(self, request, shipment_id):
        """Apply shipment status transition."""
        serializer = ShipmentStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = LogisticsService()
        shipment = service.update_status(
            actor=request.user,
            shipment_id=shipment_id,
            status=serializer.validated_data['status'],
            location_note=serializer.validated_data.get('location_note', ''),
            delivery_proof=serializer.validated_data.get('delivery_proof', ''),
        )
        return Response(ShipmentSerializer(shipment).data, status=status.HTTP_200_OK)


class ShipmentCancelView(APIView):
    """Cancel active shipment."""

    permission_classes = [permissions.IsAuthenticated, IsVerifiedRole]

    def post(self, request, shipment_id):
        """Cancel shipment with required reason."""
        serializer = ShipmentCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = LogisticsService()
        shipment = service.cancel_shipment(
            actor=request.user,
            shipment_id=shipment_id,
            reason=serializer.validated_data['reason'],
        )
        return Response(ShipmentSerializer(shipment).data, status=status.HTTP_200_OK)


class ShipmentConfirmDeliveryView(APIView):
    """Confirm delivery receipt for delivered shipment."""

    permission_classes = [permissions.IsAuthenticated, IsVerifiedRole]

    def post(self, request, shipment_id):
        """Confirm delivered shipment."""
        serializer = ShipmentConfirmDeliverySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = LogisticsService()
        shipment = service.confirm_delivery(
            actor=request.user,
            shipment_id=shipment_id,
            confirmation_note=serializer.validated_data.get('confirmation_note', ''),
        )
        return Response(ShipmentSerializer(shipment).data, status=status.HTTP_200_OK)
