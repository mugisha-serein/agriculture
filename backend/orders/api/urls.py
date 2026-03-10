"""URL routing for orders API."""

from django.urls import path

from orders.api.views import OrderCancelView
from orders.api.views import OrderConfirmView
from orders.api.views import OrderDetailView
from orders.api.views import OrderFulfillItemView
from orders.api.views import OrderListCreateView
from orders.api.views import SellerOrderListView

app_name = 'orders'

urlpatterns = [
    path('', OrderListCreateView.as_view(), name='buyer-orders'),
    path('seller/', SellerOrderListView.as_view(), name='seller-orders'),
    path('<int:order_id>/', OrderDetailView.as_view(), name='detail'),
    path('<int:order_id>/confirm/', OrderConfirmView.as_view(), name='confirm'),
    path('<int:order_id>/cancel/', OrderCancelView.as_view(), name='cancel'),
    path(
        '<int:order_id>/items/<int:item_id>/fulfill/',
        OrderFulfillItemView.as_view(),
        name='fulfill-item',
    ),
]
