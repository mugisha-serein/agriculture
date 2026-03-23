"""URL routing for reputation API."""

from django.urls import path

from reputation.api.views import ReputationLeaderboardView
from reputation.api.views import ReviewCreateView
from reputation.api.views import ReviewFlagView
from reputation.api.views import ReviewVoteView
from reputation.api.views import SellerBadgeListView
from reputation.api.views import UserReputationSummaryView
from reputation.api.views import UserReviewListView

app_name = 'reputation'

urlpatterns = [
    path('reviews/', ReviewCreateView.as_view(), name='create-review'),
    path('users/<int:user_id>/reviews/', UserReviewListView.as_view(), name='user-reviews'),
    path(
        'users/<int:user_id>/summary/',
        UserReputationSummaryView.as_view(),
        name='user-summary',
    ),
    path('users/<int:user_id>/badges/', SellerBadgeListView.as_view(), name='user-badges'),
    path('votes/', ReviewVoteView.as_view(), name='review-vote'),
    path('flags/', ReviewFlagView.as_view(), name='review-flag'),
    path('leaderboard/', ReputationLeaderboardView.as_view(), name='leaderboard'),
]
