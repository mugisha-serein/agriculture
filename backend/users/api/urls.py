"""Identity API URL configuration."""

from django.urls import path

from users.api.views import ActivationView
from users.api.views import LoginView
from users.api.views import LogoutView
from users.api.views import RefreshView
from users.api.views import RegistrationView
from users.api.views import TokenVerifyView

app_name = 'identity'

urlpatterns = [
    path('register/', RegistrationView.as_view(), name='register'),
    path('activate/', ActivationView.as_view(), name='activate'),
    path('login/', LoginView.as_view(), name='login'),
    path('refresh/', RefreshView.as_view(), name='refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('verify/', TokenVerifyView.as_view(), name='verify'),
]
