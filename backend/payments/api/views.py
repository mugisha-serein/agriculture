"""API views for payments and escrow workflows."""

from rest_framework import permissions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from payments.api.permissions import IsPaymentAdmin
from payments.api.serializers import PaymentInitiateSerializer
from payments.api.serializers import PaymentListQuerySerializer
from payments.api.serializers import PaymentRefundSerializer
from payments.api.serializers import PaymentReleaseSerializer
from payments.api.serializers import PaymentSerializer
from payments.api.serializers import PaymentWebhookSerializer
from payments.services.payment_service import PaymentService


class PaymentInitiateView(APIView):
    """Initiate idempotent payment for an order."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Create or return an idempotent payment."""
        serializer = PaymentInitiateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = PaymentService()
        payment, created = service.initiate_payment(actor=request.user, **serializer.validated_data)
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(PaymentSerializer(payment).data, status=response_status)


class PaymentListView(APIView):
    """List payments visible to current actor."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Return payments for actor or full list for admin."""
        query_serializer = PaymentListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        service = PaymentService()
        payments = service.list_payments(actor=request.user, **query_serializer.validated_data)
        return Response(PaymentSerializer(payments, many=True).data, status=status.HTTP_200_OK)


class PaymentDetailView(APIView):
    """Return one payment details for authorized actor."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, payment_id):
        """Retrieve payment by identifier."""
        service = PaymentService()
        payment = service.get_payment(actor=request.user, payment_id=payment_id)
        return Response(PaymentSerializer(payment).data, status=status.HTTP_200_OK)


class PaymentReleaseView(APIView):
    """Release escrow funds for held payments."""

    permission_classes = [permissions.IsAuthenticated, IsPaymentAdmin]

    def post(self, request, payment_id):
        """Release escrow for payment identifier."""
        serializer = PaymentReleaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = PaymentService()
        payment = service.release_escrow(
            actor=request.user,
            payment_id=payment_id,
            metadata=serializer.validated_data.get('metadata'),
        )
        return Response(PaymentSerializer(payment).data, status=status.HTTP_200_OK)


class PaymentRefundView(APIView):
    """Refund escrow-held payment to buyer."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, payment_id):
        """Refund payment by identifier."""
        serializer = PaymentRefundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = PaymentService()
        payment = service.refund_payment(
            actor=request.user,
            payment_id=payment_id,
            reason=serializer.validated_data['reason'],
        )
        return Response(PaymentSerializer(payment).data, status=status.HTTP_200_OK)


class PaymentWebhookView(APIView):
    """Receive and process provider webhook events."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Apply webhook event to payment state and escrow ledger."""
        serializer = PaymentWebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = PaymentService()
        payment, processed = service.process_webhook_event(**serializer.validated_data)
        return Response(
            {
                'processed': processed,
                'payment': PaymentSerializer(payment).data,
            },
            status=status.HTTP_200_OK,
        )
