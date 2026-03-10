"""URL routing for payments API."""

from django.urls import path

from payments.api.views import PaymentDetailView
from payments.api.views import PaymentInitiateView
from payments.api.views import PaymentListView
from payments.api.views import PaymentRefundView
from payments.api.views import PaymentReleaseView
from payments.api.views import PaymentWebhookView

app_name = 'payments'

urlpatterns = [
    path('', PaymentListView.as_view(), name='list'),
    path('initiate/', PaymentInitiateView.as_view(), name='initiate'),
    path('webhooks/', PaymentWebhookView.as_view(), name='webhook'),
    path('<int:payment_id>/', PaymentDetailView.as_view(), name='detail'),
    path('<int:payment_id>/release/', PaymentReleaseView.as_view(), name='release'),
    path('<int:payment_id>/refund/', PaymentRefundView.as_view(), name='refund'),
]
