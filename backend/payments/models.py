"""Payments domain models for escrow and immutable financial ledger."""

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from payments.domain.statuses import EscrowTransactionType
from payments.domain.statuses import PaymentStatus


class TimestampedModel(models.Model):
    """Abstract model with audit timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Payment(TimestampedModel):
    """Payment aggregate for escrow workflow and idempotency controls."""

    payment_reference = models.CharField(max_length=40, unique=True)
    order = models.OneToOneField('orders.Order', on_delete=models.PROTECT, related_name='payment')
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='payments',
    )
    status = models.CharField(max_length=16, choices=PaymentStatus.choices, default=PaymentStatus.INITIATED)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=8, default='ZAR')
    idempotency_key = models.CharField(max_length=120)
    request_fingerprint = models.CharField(max_length=64)
    provider = models.CharField(max_length=64, default='mock_gateway')
    provider_payment_id = models.CharField(max_length=128, blank=True)
    failure_code = models.CharField(max_length=64, blank=True)
    failure_message = models.CharField(max_length=255, blank=True)
    initiated_at = models.DateTimeField(default=timezone.now)
    escrow_held_at = models.DateTimeField(blank=True, null=True)
    released_at = models.DateTimeField(blank=True, null=True)
    refunded_at = models.DateTimeField(blank=True, null=True)
    processed_webhook_ids = models.JSONField(default=list)

    class Meta:
        db_table = 'payments'
        ordering = ['-initiated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['buyer', 'idempotency_key'],
                name='unique_payment_idempotency_per_buyer',
            )
        ]

    def __str__(self):
        """Return readable payment reference string."""
        return self.payment_reference


class EscrowTransaction(models.Model):
    """Immutable escrow ledger record for financial events."""

    transaction_reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name='escrow_transactions')
    transaction_type = models.CharField(max_length=16, choices=EscrowTransactionType.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=8, default='ZAR')
    external_reference = models.CharField(max_length=120, blank=True, unique=True)
    metadata = models.JSONField(default=dict)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_escrow_transactions',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = 'escrow_transactions'
        ordering = ['created_at']

    def save(self, *args, **kwargs):
        """Persist immutable transaction on create only."""
        if self.pk is not None and EscrowTransaction.objects.filter(pk=self.pk).exists():
            raise ValidationError('Escrow transaction records are immutable.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Disallow transaction deletion to preserve ledger immutability."""
        raise ValidationError('Escrow transaction records are immutable.')

    def __str__(self):
        """Return readable escrow transaction identifier."""
        return str(self.transaction_reference)
