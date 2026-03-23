"""URL routing for logistics API."""

from django.urls import path

from logistics.api.views import DeliveryRoutePlanView
from logistics.api.views import ShipmentAssignView
from logistics.api.views import ShipmentCancelView
from logistics.api.views import ShipmentConfirmDeliveryView
from logistics.api.views import ShipmentDetailView
from logistics.api.views import ShipmentListCreateView
from logistics.api.views import ShipmentStatusUpdateView
from logistics.api.views import ShipmentTrackingEventView

app_name = 'logistics'

urlpatterns = [
    path('shipments/', ShipmentListCreateView.as_view(), name='shipments'),
    path('shipments/<int:shipment_id>/', ShipmentDetailView.as_view(), name='shipment-detail'),
    path('shipments/<int:shipment_id>/assign/', ShipmentAssignView.as_view(), name='assign'),
    path('shipments/<int:shipment_id>/status/', ShipmentStatusUpdateView.as_view(), name='status'),
    path('shipments/<int:shipment_id>/cancel/', ShipmentCancelView.as_view(), name='cancel'),
    path(
        'shipments/<int:shipment_id>/confirm-delivery/',
        ShipmentConfirmDeliveryView.as_view(),
        name='confirm-delivery',
    ),
    path('shipments/<int:shipment_id>/tracking/', ShipmentTrackingEventView.as_view(), name='tracking'),
    path('routes/plan/', DeliveryRoutePlanView.as_view(), name='route-plan'),
]
