"""Reputation models for user reviews and ratings."""

from django.conf import settings
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F
from django.db.models import Q

from reputation.domain.scoring import MAX_RATING
from reputation.domain.scoring import MIN_RATING


class TimestampedModel(models.Model):
    """Abstract model with audit timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Review(TimestampedModel):
    """Review record representing one rating from reviewer to reviewee."""

    order = models.ForeignKey('orders.Order', on_delete=models.PROTECT, related_name='reviews')
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_given',
    )
    reviewee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_received',
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MIN_RATING), MaxValueValidator(MAX_RATING)]
    )
    comment = models.TextField(blank=True)
    is_visible = models.BooleanField(default=True)

    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'reviewer', 'reviewee'],
                name='unique_review_per_order_reviewer_reviewee',
            ),
            models.CheckConstraint(
                condition=~Q(reviewer=F('reviewee')),
                name='reviews_reviewer_not_reviewee',
            ),
        ]

    def __str__(self):
        """Return readable representation of review."""
        return f'{self.order.order_number}:{self.reviewer_id}->{self.reviewee_id}'
