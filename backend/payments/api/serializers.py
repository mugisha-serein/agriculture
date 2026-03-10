"""Serializers for payments API workflows."""

from rest_framework import serializers

from payments.domain.statuses import PaymentStatus
from payments.models import EscrowTransaction
from payments.models import Payment


class PaymentInitiateSerializer(serializers.Serializer):
    """Input serializer for payment initiation."""

    order_id = serializers.IntegerField()
    idempotency_key = serializers.CharField(max_length=120)
    provider = serializers.CharField(max_length=64, required=False, default='mock_gateway')
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, required=False)
    currency = serializers.CharField(max_length=8, required=False, default='ZAR')


class PaymentListQuerySerializer(serializers.Serializer):
    """Query serializer for payment listing filters."""

    status = serializers.ChoiceField(choices=PaymentStatus.choices, required=False)


class EscrowTransactionSerializer(serializers.ModelSerializer):
    """Output serializer for immutable escrow transaction rows."""

    created_by_id = serializers.IntegerField(source='created_by.id', allow_null=True, read_only=True)

    class Meta:
        model = EscrowTransaction
        fields = (
            'id',
            'transaction_reference',
            'transaction_type',
            'amount',
            'currency',
            'external_reference',
            'metadata',
            'created_by_id',
            'created_at',
        )


class PaymentSerializer(serializers.ModelSerializer):
    """Output serializer for payment aggregate details."""

    order_id = serializers.IntegerField(source='order.id', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    buyer_id = serializers.IntegerField(source='buyer.id', read_only=True)
    buyer_first_name = serializers.CharField(source='buyer.first_name', read_only=True)
    buyer_last_name = serializers.CharField(source='buyer.last_name', read_only=True)
    buyer_email = serializers.EmailField(source='buyer.email', read_only=True)
    escrow_transactions = EscrowTransactionSerializer(many=True, read_only=True)

    class Meta:
        model = Payment
        fields = (
            'id',
            'payment_reference',
            'order_id',
            'order_number',
            'buyer_id',
            'buyer_first_name',
            'buyer_last_name',
            'buyer_email',
            'status',
            'amount',
            'currency',
            'idempotency_key',
            'provider',
            'provider_payment_id',
            'failure_code',
            'failure_message',
            'initiated_at',
            'escrow_held_at',
            'released_at',
            'refunded_at',
            'escrow_transactions',
        )


class PaymentRefundSerializer(serializers.Serializer):
    """Input serializer for refund requests."""

    reason = serializers.CharField()


class PaymentReleaseSerializer(serializers.Serializer):
    """Input serializer for manual escrow release requests."""

    metadata = serializers.JSONField(required=False)


class PaymentWebhookSerializer(serializers.Serializer):
    """Input serializer for payment webhook events."""

    event_id = serializers.CharField(max_length=120)
    event_type = serializers.CharField(max_length=64)
    payment_reference = serializers.CharField(max_length=40)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, required=False)
    currency = serializers.CharField(max_length=8, required=False)
    failure_code = serializers.CharField(max_length=64, required=False, allow_blank=True)
    failure_message = serializers.CharField(max_length=255, required=False, allow_blank=True)
    metadata = serializers.JSONField(required=False)
