"""Reputation workflows for review creation and Bayesian aggregation."""

from django.db import IntegrityError
from django.db import transaction
from django.db.models import Avg
from django.db.models import Count
from rest_framework.exceptions import NotFound
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError

from logistics.models import Shipment
from orders.domain.statuses import OrderStatus
from orders.models import Order
from reputation.domain.scoring import DEFAULT_PRIOR_WEIGHT
from reputation.domain.scoring import MAX_RATING
from reputation.domain.scoring import MIN_RATING
from reputation.models import Review
from users.models import User


class ReputationService:
    """Application service for trust and reputation workflows."""

    @transaction.atomic
    def create_review(self, *, actor, order_id, reviewee_id, rating, comment=''):
        """Create one review between valid order participants."""
        if not actor.is_authenticated:
            raise PermissionDenied('Authentication is required.')
        order = self._get_order(order_id=order_id)
        if order.status != OrderStatus.COMPLETED:
            raise ValidationError({'order_id': ['Reviews are allowed only for completed orders.']})

        participants = self._participant_ids_for_order(order=order)
        if actor.id not in participants:
            raise PermissionDenied('Reviewer must be a participant in the order.')
        if reviewee_id not in participants:
            raise ValidationError({'reviewee_id': ['Reviewee must be a participant in the order.']})
        if actor.id == reviewee_id:
            raise ValidationError({'reviewee_id': ['Reviewer and reviewee must be different users.']})
        if int(rating) < MIN_RATING or int(rating) > MAX_RATING:
            raise ValidationError({'rating': [f'Rating must be between {MIN_RATING} and {MAX_RATING}.']})

        try:
            review = Review.objects.create(
                order=order,
                reviewer=actor,
                reviewee_id=reviewee_id,
                rating=rating,
                comment=comment,
            )
        except IntegrityError as exc:
            raise ValidationError(
                {'review': ['A review for this order and reviewee from this reviewer already exists.']}
            ) from exc
        return review

    def list_reviews_for_user(self, *, user_id):
        """List visible received reviews for a user."""
        if not User.objects.filter(id=user_id).exists():
            raise NotFound('User was not found.')
        return Review.objects.select_related('reviewer', 'order').filter(
            reviewee_id=user_id,
            is_visible=True,
        )

    def get_reputation_summary(self, *, user_id, prior_weight=DEFAULT_PRIOR_WEIGHT):
        """Return aggregated rating summary with Bayesian score for a user."""
        user = self._get_user(user_id=user_id)
        reviews = Review.objects.filter(reviewee=user, is_visible=True)

        aggregates = reviews.aggregate(
            review_count=Count('id'),
            average_rating=Avg('rating'),
        )
        review_count = int(aggregates['review_count'] or 0)
        average_rating = float(aggregates['average_rating'] or 0.0)
        global_mean = self._global_average_rating()
        bayesian_score = self._bayesian_score(
            average_rating=average_rating,
            review_count=review_count,
            global_mean=global_mean,
            prior_weight=float(prior_weight),
        )

        distribution = {str(value): 0 for value in range(MIN_RATING, MAX_RATING + 1)}
        for row in reviews.values('rating').annotate(count=Count('id')):
            distribution[str(row['rating'])] = row['count']

        return {
            'user_id': user.id,
            'user_email': user.email,
            'role': user.role,
            'review_count': review_count,
            'average_rating': round(average_rating, 4),
            'global_average_rating': round(global_mean, 4),
            'bayesian_score': round(bayesian_score, 4),
            'rating_distribution': distribution,
        }

    def leaderboard(self, *, role=None, limit=20, prior_weight=DEFAULT_PRIOR_WEIGHT, min_reviews=1):
        """Return ranked reputation leaderboard using Bayesian scores."""
        reviews = Review.objects.filter(is_visible=True).values(
            'reviewee_id',
            'reviewee__email',
            'reviewee__role',
        ).annotate(
            review_count=Count('id'),
            average_rating=Avg('rating'),
        )
        if role:
            reviews = reviews.filter(reviewee__role=role)

        global_mean = self._global_average_rating()
        rows = []
        for row in reviews:
            review_count = int(row['review_count'] or 0)
            if review_count < int(min_reviews):
                continue
            avg_rating = float(row['average_rating'] or 0.0)
            score = self._bayesian_score(
                average_rating=avg_rating,
                review_count=review_count,
                global_mean=global_mean,
                prior_weight=float(prior_weight),
            )
            rows.append(
                {
                    'user_id': row['reviewee_id'],
                    'user_email': row['reviewee__email'],
                    'role': row['reviewee__role'],
                    'review_count': review_count,
                    'average_rating': round(avg_rating, 4),
                    'bayesian_score': round(score, 4),
                }
            )
        rows.sort(key=lambda value: (-value['bayesian_score'], -value['review_count'], value['user_id']))
        return rows[: int(limit)]

    def _participant_ids_for_order(self, *, order):
        """Return set of all participant user IDs for an order."""
        participant_ids = {order.buyer_id}
        participant_ids.update(order.items.values_list('seller_id', flat=True))
        participant_ids.update(
            Shipment.objects.filter(order=order, transporter_id__isnull=False).values_list(
                'transporter_id',
                flat=True,
            )
        )
        return participant_ids

    def _bayesian_score(self, *, average_rating, review_count, global_mean, prior_weight):
        """Compute Bayesian adjusted rating score."""
        reviews_weight = float(review_count)
        prior = float(prior_weight)
        if reviews_weight + prior <= 0:
            return float(global_mean)
        return ((reviews_weight / (reviews_weight + prior)) * average_rating) + (
            (prior / (reviews_weight + prior)) * global_mean
        )

    def _global_average_rating(self):
        """Return global mean rating over all visible reviews."""
        value = Review.objects.filter(is_visible=True).aggregate(avg=Avg('rating'))['avg']
        if value is None:
            midpoint = (MIN_RATING + MAX_RATING) / 2
            return float(midpoint)
        return float(value)

    def _get_order(self, *, order_id):
        """Return order by identifier with item prefetch."""
        try:
            return Order.objects.prefetch_related('items').get(id=order_id)
        except Order.DoesNotExist as exc:
            raise NotFound('Order was not found.') from exc

    def _get_user(self, *, user_id):
        """Return user by identifier."""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist as exc:
            raise NotFound('User was not found.') from exc
