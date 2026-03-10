"""URL configuration for verification API endpoints."""

from django.urls import path

from verification.api.views import AdminPendingVerificationListView
from verification.api.views import AdminReviewVerificationView
from verification.api.views import MyVerificationView
from verification.api.views import SubmitVerificationView

app_name = 'verification'

urlpatterns = [
    path('submit/', SubmitVerificationView.as_view(), name='submit'),
    path('me/', MyVerificationView.as_view(), name='me'),
    path('admin/pending/', AdminPendingVerificationListView.as_view(), name='admin-pending'),
    path(
        'admin/<int:verification_id>/review/',
        AdminReviewVerificationView.as_view(),
        name='admin-review',
    ),
]
