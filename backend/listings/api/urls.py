"""URL configuration for marketplace API endpoints."""

from django.urls import path

from listings.api.views import CropDetailView
from listings.api.views import CropListCreateView
from listings.api.views import MyProductListView
from listings.api.views import ProductDetailView
from listings.api.views import ProductListCreateView

app_name = 'marketplace'

urlpatterns = [
    path('crops/', CropListCreateView.as_view(), name='crops'),
    path('crops/<int:crop_id>/', CropDetailView.as_view(), name='crop-detail'),
    path('products/', ProductListCreateView.as_view(), name='products'),
    path('products/me/', MyProductListView.as_view(), name='my-products'),
    path('products/<int:product_id>/', ProductDetailView.as_view(), name='product-detail'),
]
