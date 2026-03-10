"""Serializers for reputation APIs."""

from rest_framework import serializers

from reputation.models import Review


class ReviewCreateSerializer(serializers.Serializer):
    """Input serializer for review creation."""

    order_id = serializers.IntegerField()
    reviewee_id = serializers.IntegerField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True)


class ReputationQuerySerializer(serializers.Serializer):
    """Query serializer for leaderboard parameters."""

    role = serializers.ChoiceField(
        choices=['buyer', 'seller', 'transporter', 'admin'],
        required=False,
    )
    limit = serializers.IntegerField(min_value=1, max_value=100, default=20)
    prior_weight = serializers.FloatField(min_value=0.0, default=5.0)
    min_reviews = serializers.IntegerField(min_value=0, default=1)


class ReviewSerializer(serializers.ModelSerializer):
    """Output serializer for review record details."""

    reviewer_id = serializers.IntegerField(source='reviewer.id', read_only=True)
    reviewer_email = serializers.EmailField(source='reviewer.email', read_only=True)
    reviewee_id = serializers.IntegerField(source='reviewee.id', read_only=True)
    reviewee_email = serializers.EmailField(source='reviewee.email', read_only=True)
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)

    class Meta:
        model = Review
        fields = (
            'id',
            'order_id',
            'order_number',
            'reviewer_id',
            'reviewer_email',
            'reviewee_id',
            'reviewee_email',
            'rating',
            'comment',
            'created_at',
        )
