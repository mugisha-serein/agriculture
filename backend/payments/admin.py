"""Admin registrations for payments models."""

from django.contrib import admin

from payments.models import EscrowTransaction
from payments.models import Payment


class EscrowTransactionInline(admin.TabularInline):
    """Inline display for immutable escrow transactions."""

    model = EscrowTransaction
    extra = 0
    can_delete = False
    readonly_fields = (
        'transaction_reference',
        'transaction_type',
        'amount',
        'currency',
        'external_reference',
        'metadata',
        'created_by',
        'created_at',
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin configuration for payment aggregates."""

    list_display = (
        'id',
        'payment_reference',
        'order',
        'buyer',
        'status',
        'amount',
        'currency',
        'provider',
        'initiated_at',
    )
    list_filter = ('status', 'provider', 'currency')
    search_fields = ('payment_reference', 'order__order_number', 'buyer__email', 'idempotency_key')
    ordering = ('-initiated_at',)
    inlines = [EscrowTransactionInline]


@admin.register(EscrowTransaction)
class EscrowTransactionAdmin(admin.ModelAdmin):
    """Admin configuration for escrow ledger records."""

    list_display = (
        'id',
        'transaction_reference',
        'payment',
        'transaction_type',
        'amount',
        'currency',
        'external_reference',
        'created_at',
    )
    list_filter = ('transaction_type', 'currency')
    search_fields = ('payment__payment_reference', 'external_reference')
    ordering = ('created_at',)
    readonly_fields = (
        'transaction_reference',
        'payment',
        'transaction_type',
        'amount',
        'currency',
        'external_reference',
        'metadata',
        'created_by',
        'created_at',
    )
