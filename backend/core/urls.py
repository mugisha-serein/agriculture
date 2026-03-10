"""URL routing for the core project."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/identity/', include('users.api.urls')),
    path('api/verification/', include('verification.api.urls')),
    path('api/marketplace/', include('listings.api.urls')),
    path('api/discovery/', include('discovery.api.urls')),
    path('api/orders/', include('orders.api.urls')),
    path('api/payments/', include('payments.api.urls')),
    path('api/logistics/', include('logistics.api.urls')),
    path('api/reputation/', include('reputation.api.urls')),
    path('api/audit/', include('audit.api.urls')),
    path('api/dashboard/', include('dashboard.api.urls')),
]
