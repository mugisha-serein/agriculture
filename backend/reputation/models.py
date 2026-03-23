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
    is_verified_purchase = models.BooleanField(default=False)

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


class ReviewVote(TimestampedModel):
    """Helpful/unhelpful vote cast on a review."""

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='votes',
    )
    voter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='review_votes',
    )
    is_helpful = models.BooleanField()

    class Meta:
        db_table = 'review_votes'
        unique_together = ('review', 'voter')

    def __str__(self):
        return f'{self.voter.email} -> {self.review_id} ({self.is_helpful})'


class ReviewFlag(TimestampedModel):
    """Flag submitted on a review to mark manipulation."""

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='flags',
    )
    flagged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='review_flags',
    )
    reason = models.TextField()
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='resolved_review_flags',
        null=True,
        blank=True,
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'review_flags'
        unique_together = ('review', 'flagged_by')

    def __str__(self):
        return f'Flag by {self.flagged_by.email} on {self.review_id}'


class ReputationScore(TimestampedModel):
    """Cached reputation score that incorporates trust signals."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reputation_score',
    )
    bayesian_score = models.DecimalField(max_digits=5, decimal_places=4, default=0.0)
    average_rating = models.DecimalField(max_digits=5, decimal_places=4, default=0.0)
    review_count = models.PositiveIntegerField(default=0)
    verified_purchase_reviews = models.PositiveIntegerField(default=0)
    review_helpfulness = models.DecimalField(max_digits=5, decimal_places=4, default=0.0)
    reviewer_reputation = models.DecimalField(max_digits=5, decimal_places=4, default=0.0)

    class Meta:
        db_table = 'reputation_scores'

    def __str__(self):
        return f'{self.user.email} score={self.bayesian_score}'


class SellerBadge(TimestampedModel):
    """Badges awarded to high-trust sellers."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='seller_badges',
    )
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    awarded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'seller_badges'
        unique_together = ('user', 'name')

    def __str__(self):
        return f'{self.user.email} badge={self.name}'
