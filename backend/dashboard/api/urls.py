from django.urls import path
from dashboard.api.views import AnalyticsOverviewView
from dashboard.api.views import DashboardView

app_name = 'dashboard'

urlpatterns = [
    path('stats/', DashboardView.as_view(), name='dashboard-stats'),
    path('analytics/', AnalyticsOverviewView.as_view(), name='dashboard-analytics'),
]
