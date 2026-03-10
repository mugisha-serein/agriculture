"""Marketplace app API tests."""

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from listings.domain.statuses import ListingStatus
from listings.models import Crop, Product
from users.models import User


class MarketplaceApiTests(APITestCase):
    """End-to-end tests for marketplace listing workflows."""

    def setUp(self):
        """Set up users and crop fixtures for marketplace tests."""
        self.seller = User.objects.create_user(
            email='seller@example.com',
            full_name='Seller One',
            password='StrongPass123',
            role='seller',
            is_active=True,
        )
        self.other_seller = User.objects.create_user(
            email='seller2@example.com',
            full_name='Seller Two',
            password='StrongPass123',
            role='seller',
            is_active=True,
        )
        self.buyer = User.objects.create_user(
            email='buyer@example.com',
            full_name='Buyer One',
            password='StrongPass123',
            role='buyer',
            is_active=True,
        )
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            full_name='Admin One',
            password='StrongPass123',
            role='admin',
            is_active=True,
            is_staff=True,
        )
        self.crop = Crop.objects.create(name='Maize', slug='maize', description='White maize')

    def test_seller_can_create_update_and_delete_product(self):
        """Seller can manage own product listing lifecycle."""
        self.client.force_authenticate(user=self.seller)
        create_response = self.client.post(
            reverse('marketplace:products'),
            data={
                'crop_id': self.crop.id,
                'title': 'Fresh Maize',
                'description': 'Farm harvest',
                'unit': 'kg',
                'price_per_unit': '12.50',
                'quantity_available': '500.000',
                'minimum_order_quantity': '10.000',
                'location_name': 'Johannesburg',
                'latitude': '-26.204100',
                'longitude': '28.047300',
                'expires_at': (timezone.now() + timedelta(days=5)).isoformat(),
                'status': 'active',
            },
            format='json',
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        product_id = create_response.data['id']

        update_response = self.client.patch(
            reverse('marketplace:product-detail', kwargs={'product_id': product_id}),
            data={'quantity_available': '0.000'},
            format='json',
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data['status'], ListingStatus.SOLD_OUT)

        delete_response = self.client.delete(
            reverse('marketplace:product-detail', kwargs={'product_id': product_id})
        )
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

        list_response = self.client.get(reverse('marketplace:products'))
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 0)

    def test_buyer_cannot_create_product(self):
        """Buyer cannot create marketplace product listings."""
        self.client.force_authenticate(user=self.buyer)
        response = self.client.post(
            reverse('marketplace:products'),
            data={
                'crop_id': self.crop.id,
                'title': 'Tomatoes',
                'unit': 'kg',
                'price_per_unit': '8.00',
                'quantity_available': '100.000',
                'minimum_order_quantity': '5.000',
                'location_name': 'Pretoria',
                'expires_at': (timezone.now() + timedelta(days=2)).isoformat(),
                'status': 'active',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_only_owner_or_admin_can_update_product(self):
        """Non-owner seller is forbidden while admin can update listing."""
        product = Product.objects.create(
            seller=self.seller,
            crop=self.crop,
            title='Beans',
            unit='kg',
            price_per_unit='15.00',
            quantity_available='50.000',
            minimum_order_quantity='5.000',
            location_name='Durban',
            expires_at=timezone.now() + timedelta(days=3),
            status=ListingStatus.ACTIVE,
        )

        self.client.force_authenticate(user=self.other_seller)
        forbidden = self.client.patch(
            reverse('marketplace:product-detail', kwargs={'product_id': product.id}),
            data={'title': 'Changed'},
            format='json',
        )
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin_user)
        allowed = self.client.patch(
            reverse('marketplace:product-detail', kwargs={'product_id': product.id}),
            data={'title': 'Admin Updated'},
            format='json',
        )
        self.assertEqual(allowed.status_code, status.HTTP_200_OK)
        self.assertEqual(allowed.data['title'], 'Admin Updated')

    def test_expired_products_are_hidden_and_marked_expired(self):
        """Expired listings are excluded from available results and status is updated."""
        product = Product.objects.create(
            seller=self.seller,
            crop=self.crop,
            title='Cabbage',
            unit='kg',
            price_per_unit='6.00',
            quantity_available='30.000',
            minimum_order_quantity='2.000',
            location_name='Bloemfontein',
            expires_at=timezone.now() + timedelta(days=1),
            status=ListingStatus.ACTIVE,
        )
        Product.objects.filter(id=product.id).update(expires_at=timezone.now() - timedelta(minutes=1))

        response = self.client.get(reverse('marketplace:products'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        product.refresh_from_db()
        self.assertEqual(product.status, ListingStatus.EXPIRED)

    def test_geo_filter_returns_nearby_products(self):
        """Radius filter should return only nearby listings."""
        Product.objects.create(
            seller=self.seller,
            crop=self.crop,
            title='Nearby Product',
            unit='kg',
            price_per_unit='9.00',
            quantity_available='90.000',
            minimum_order_quantity='5.000',
            location_name='Johannesburg',
            latitude='-26.204100',
            longitude='28.047300',
            expires_at=timezone.now() + timedelta(days=2),
            status=ListingStatus.ACTIVE,
        )
        Product.objects.create(
            seller=self.seller,
            crop=self.crop,
            title='Far Product',
            unit='kg',
            price_per_unit='9.00',
            quantity_available='90.000',
            minimum_order_quantity='5.000',
            location_name='Cape Town',
            latitude='-33.924900',
            longitude='18.424100',
            expires_at=timezone.now() + timedelta(days=2),
            status=ListingStatus.ACTIVE,
        )

        response = self.client.get(
            reverse('marketplace:products'),
            data={
                'latitude': '-26.204100',
                'longitude': '28.047300',
                'radius_km': '60.00',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Nearby Product')
