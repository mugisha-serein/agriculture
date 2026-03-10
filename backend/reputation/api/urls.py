"""URL routing for reputation API."""

from django.urls import path

from reputation.api.views import ReputationLeaderboardView
from reputation.api.views import ReviewCreateView
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
    path('leaderboard/', ReputationLeaderboardView.as_view(), name='leaderboard'),
]
