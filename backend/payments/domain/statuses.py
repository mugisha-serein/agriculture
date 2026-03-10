"""Payment and escrow lifecycle status definitions."""

from django.db.models import TextChoices


class PaymentStatus(TextChoices):
    """Lifecycle statuses for payment records."""

    INITIATED = 'initiated', 'Initiated'
    ESCROW_HELD = 'escrow_held', 'Escrow Held'
    RELEASED = 'released', 'Released'
    REFUNDED = 'refunded', 'Refunded'
    FAILED = 'failed', 'Failed'


class EscrowTransactionType(TextChoices):
    """Escrow ledger transaction types."""

    HOLD = 'hold', 'Hold'
    RELEASE = 'release', 'Release'
    REFUND = 'refund', 'Refund'
