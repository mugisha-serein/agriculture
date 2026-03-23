"""Reputation workflows for review creation and Bayesian aggregation."""

from decimal import Decimal

from django.db import IntegrityError
from django.db import transaction
from django.db.models import Avg
from django.db.models import Count
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import NotFound
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError

from logistics.models import Shipment
from orders.domain.statuses import OrderStatus
from orders.models import Order
from reputation.domain.scoring import DEFAULT_PRIOR_WEIGHT
from reputation.domain.scoring import MAX_RATING
from reputation.domain.scoring import MIN_RATING
from reputation.domain.scoring import bayesian_average
from reputation.domain.scoring import weighted_bayesian_average
from reputation.models import ReputationScore
from reputation.models import Review
from reputation.models import ReviewFlag
from reputation.models import ReviewVote
from reputation.models import SellerBadge
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
                is_verified_purchase=(actor.id == order.buyer_id),
            )
        except IntegrityError as exc:
            raise ValidationError(
                {'review': ['A review for this order and reviewee from this reviewer already exists.']}
            ) from exc
        self._update_reputation_score(user_id=review.reviewee_id)
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
        score = ReputationScore.objects.filter(user_id=user_id).first()
        if not score:
            score = self._update_reputation_score(user_id=user_id)
        reviews = Review.objects.filter(reviewee=user, is_visible=True)

        distribution = {str(value): 0 for value in range(MIN_RATING, MAX_RATING + 1)}
        for row in reviews.values('rating').annotate(count=Count('id')):
            distribution[str(row['rating'])] = row['count']

        return {
            'user_id': user.id,
            'user_email': user.email,
            'role': user.role,
            'review_count': score.review_count,
            'average_rating': float(score.average_rating),
            'global_average_rating': round(self._global_average_rating(), 4),
            'bayesian_score': float(score.bayesian_score),
            'rating_distribution': distribution,
            'verified_purchase_reviews': score.verified_purchase_reviews,
            'review_helpfulness': float(score.review_helpfulness),
            'reviewer_reputation': float(score.reviewer_reputation),
            'badges': self._get_badges(user_id=user_id),
        }

    def leaderboard(self, *, role=None, limit=20, prior_weight=DEFAULT_PRIOR_WEIGHT, min_reviews=1):
        """Return ranked reputation leaderboard using Bayesian scores."""
        scores = ReputationScore.objects.select_related('user')
        if role:
            scores = scores.filter(user__role=role)
        rows = []
        for score in scores:
            if score.review_count < int(min_reviews):
                continue
            rows.append(
                {
                    'user_id': score.user_id,
                    'user_email': score.user.email,
                    'role': score.user.role,
                    'review_count': score.review_count,
                    'average_rating': float(score.average_rating),
                    'bayesian_score': float(score.bayesian_score),
                }
            )
        rows.sort(key=lambda value: (-value['bayesian_score'], -value['review_count'], value['user_id']))
        return rows[: int(limit)]

    def record_review_vote(self, *, actor, review_id, is_helpful):
        """Allow actors to mark reviews as helpful/unhelpful."""
        if not actor.is_authenticated:
            raise PermissionDenied('Authentication is required.')
        review = self._get_visible_review(review_id=review_id)
        if actor.id == review.reviewer_id:
            raise PermissionDenied('Reviewers cannot vote on their own reviews.')
        vote, created = ReviewVote.objects.update_or_create(
            review=review,
            voter=actor,
            defaults={'is_helpful': is_helpful},
        )
        self._update_reputation_score(user_id=review.reviewee_id)
        return vote

    def flag_review(self, *, actor, review_id, reason):
        """Allow actors to flag suspicious reviews."""
        if not actor.is_authenticated:
            raise PermissionDenied('Authentication is required.')
        review = self._get_review(review_id=review_id)
        if actor.id == review.reviewer_id:
            raise PermissionDenied('Reviewers cannot flag their own review.')
        flag, created = ReviewFlag.objects.get_or_create(
            review=review,
            flagged_by=actor,
            defaults={'reason': reason},
        )
        if not created:
            raise ValidationError({'flag': ['You have already flagged this review.']})
        self._evaluate_flags(review=review)
        return flag

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

    def _global_average_rating(self):
        """Return global mean rating over all visible reviews."""
        value = Review.objects.filter(is_visible=True).aggregate(avg=Avg('rating'))['avg']
        if value is None:
            midpoint = (MIN_RATING + MAX_RATING) / 2
            return float(midpoint)
        return float(value)

    def _update_reputation_score(self, *, user_id):
        reviews = Review.objects.filter(reviewee_id=user_id, is_visible=True)
        aggregates = reviews.aggregate(
            review_count=Count('id'),
            average_rating=Avg('rating'),
        )
        review_count = int(aggregates['review_count'] or 0)
        average_rating = float(aggregates['average_rating'] or 0.0)
        verified_purchase_reviews = reviews.filter(is_verified_purchase=True).count()
        helpful_votes = ReviewVote.objects.filter(review__reviewee_id=user_id, is_helpful=True).count()
        total_votes = ReviewVote.objects.filter(review__reviewee_id=user_id).count()
        helpfulness_ratio = float(helpful_votes / total_votes) if total_votes else 0.0
        reviewer_reputation = self._reviewer_reputation_average(reviews)
        global_mean = self._global_average_rating()
        base_score = bayesian_average(
            average_rating=average_rating,
            review_count=review_count,
            global_mean=global_mean,
            prior_weight=DEFAULT_PRIOR_WEIGHT,
        )
        weighted_score = weighted_bayesian_average(
            base_score=base_score,
            helpfulness_ratio=helpfulness_ratio,
            verified_ratio=(verified_purchase_reviews / review_count) if review_count else 0.0,
            reviewer_reputation=reviewer_reputation,
        )
        score_values = {
            'bayesian_score': Decimal(str(weighted_score)),
            'average_rating': Decimal(str(average_rating)),
            'review_count': review_count,
            'verified_purchase_reviews': verified_purchase_reviews,
            'review_helpfulness': Decimal(str(helpfulness_ratio)),
            'reviewer_reputation': Decimal(str(reviewer_reputation)),
            'updated_at': timezone.now(),
        }
        score, _ = ReputationScore.objects.update_or_create(user_id=user_id, defaults=score_values)
        self._award_badges(user_id=user_id, score=score)
        return score

    def _reviewer_reputation_average(self, reviews):
        reviewer_ids = list(set(reviews.values_list('reviewer_id', flat=True)))
        if not reviewer_ids:
            return 0.0
        scores = ReputationScore.objects.filter(user_id__in=reviewer_ids)
        if scores.exists():
            return float(sum(float(score.bayesian_score) for score in scores) / scores.count())
        fallback = Review.objects.filter(reviewee_id__in=reviewer_ids, is_visible=True).aggregate(
            average_rating=Avg('rating')
        )['average_rating']
        if fallback is None:
            return 0.0
        return float(fallback)

    def _evaluate_flags(self, *, review):
        active_flags = ReviewFlag.objects.filter(review=review, is_resolved=False).count()
        if active_flags >= 3 and review.is_visible:
            review.is_visible = False
            review.updated_at = timezone.now()
            review.save(update_fields=['is_visible', 'updated_at'])
            self._update_reputation_score(user_id=review.reviewee_id)

    def _get_visible_review(self, *, review_id):
        try:
            return Review.objects.get(id=review_id, is_visible=True)
        except Review.DoesNotExist as exc:
            raise NotFound('Review was not found.') from exc

    def _get_review(self, *, review_id):
        try:
            return Review.objects.get(id=review_id)
        except Review.DoesNotExist as exc:
            raise NotFound('Review was not found.') from exc

    def _get_badges(self, *, user_id):
        return [
            {
                'name': badge.name,
                'description': badge.description,
                'awarded_at': badge.awarded_at,
            }
            for badge in SellerBadge.objects.filter(user_id=user_id, is_active=True)
        ]

    def _award_badges(self, *, user_id, score):
        badge_definitions = [
            (
                'Top Rated Seller',
                'Consistently excellent feedback.',
                lambda s: s.bayesian_score >= Decimal('4.5') and s.review_count >= 10,
            ),
            (
                'Verified Purchase Champion',
                'High number of verified purchase reviews.',
                lambda s: s.verified_purchase_reviews >= 5,
            ),
            (
                'Helpful Reviews',
                'Reviews marked helpful by the community.',
                lambda s: s.review_helpfulness >= Decimal('0.5'),
            ),
        ]
        for name, description, condition in badge_definitions:
            is_awarded = condition(score)
            badge, created = SellerBadge.objects.get_or_create(
                user_id=user_id,
                name=name,
                defaults={
                    'description': description,
                    'awarded_at': timezone.now() if is_awarded else None,
                    'is_active': is_awarded,
                },
            )
            update_fields = []
            if is_awarded and not badge.is_active:
                badge.is_active = True
                badge.awarded_at = timezone.now()
                update_fields.extend(['is_active', 'awarded_at'])
            if not is_awarded and badge.is_active:
                badge.is_active = False
                update_fields.append('is_active')
            if update_fields:
                badge.save(update_fields=update_fields)

    def get_user_badges(self, *, user_id):
        """Return active badges awarded to a user."""
        self._get_user(user_id=user_id)
        return self._get_badges(user_id=user_id)

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
