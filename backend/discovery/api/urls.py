"""URL routing for discovery API."""

from django.urls import path

from discovery.api.views import HomeView
from discovery.api.views import SearchView

app_name = 'discovery'

urlpatterns = [
    path('home/', HomeView.as_view(), name='home'),
    path('search/', SearchView.as_view(), name='search'),
]
