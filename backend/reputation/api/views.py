"""API views for reputation reviews and Bayesian aggregation."""

from rest_framework import permissions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from reputation.api.serializers import ReputationQuerySerializer
from reputation.api.serializers import ReviewCreateSerializer
from reputation.api.serializers import ReviewFlagSerializer
from reputation.api.serializers import ReviewSerializer
from reputation.api.serializers import ReviewVoteSerializer
from reputation.api.serializers import SellerBadgeSerializer
from reputation.services.reputation_service import ReputationService


class ReviewCreateView(APIView):
    """Create reviews between participants of completed orders."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Create a review from authenticated user."""
        serializer = ReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = ReputationService()
        review = service.create_review(actor=request.user, **serializer.validated_data)
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)


class ReviewVoteView(APIView):
    """Allow users to vote on review helpfulness."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ReviewVoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = ReputationService()
        vote = service.record_review_vote(actor=request.user, **serializer.validated_data)
        return Response({'id': vote.id, 'is_helpful': vote.is_helpful}, status=status.HTTP_200_OK)


class ReviewFlagView(APIView):
    """Allow users to flag suspicious reviews."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ReviewFlagSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = ReputationService()
        flag = service.flag_review(actor=request.user, **serializer.validated_data)
        return Response({'id': flag.id, 'is_resolved': flag.is_resolved}, status=status.HTTP_200_OK)


class UserReviewListView(APIView):
    """List received visible reviews for a user."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, user_id):
        """Return review records for target user."""
        service = ReputationService()
        reviews = service.list_reviews_for_user(user_id=user_id)
        return Response(ReviewSerializer(reviews, many=True).data, status=status.HTTP_200_OK)


class UserReputationSummaryView(APIView):
    """Return Bayesian reputation summary for a user."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, user_id):
        """Return aggregate summary metrics for target user."""
        prior_weight = request.query_params.get('prior_weight', 5.0)
        service = ReputationService()
        summary = service.get_reputation_summary(user_id=user_id, prior_weight=float(prior_weight))
        return Response(summary, status=status.HTTP_200_OK)


class SellerBadgeListView(APIView):
    """Return badges awarded to a seller."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, user_id):
        service = ReputationService()
        badges = service.get_user_badges(user_id=user_id)
        return Response(SellerBadgeSerializer(badges, many=True).data, status=status.HTTP_200_OK)

class ReputationLeaderboardView(APIView):
    """Return ranked leaderboard using Bayesian reputation score."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Return leaderboard rankings with optional role filtering."""
        serializer = ReputationQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        service = ReputationService()
        results = service.leaderboard(**serializer.validated_data)
        return Response({'results': results}, status=status.HTTP_200_OK)
