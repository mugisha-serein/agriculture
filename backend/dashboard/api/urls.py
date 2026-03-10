from django.urls import path
from dashboard.api.views import DashboardView

app_name = 'dashboard'

urlpatterns = [
    path('stats/', DashboardView.as_view(), name='dashboard-stats'),
]
