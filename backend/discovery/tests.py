"""Discovery app API tests."""

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from discovery.models import SearchQueryLog
from listings.domain.statuses import ListingStatus
from listings.models import Crop, Product, ProductInventory, ProductPricing
from users.models import User


class DiscoveryApiTests(APITestCase):
    """End-to-end tests for discovery search flows."""

    def setUp(self):
        """Create fixtures for discovery queries and ranking."""
        self.seller = User.objects.create_user(
            email='seller@example.com',
            full_name='Seller One',
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
        self.maize = Crop.objects.create(name='Maize', slug='maize')
        self.beans = Crop.objects.create(name='Beans', slug='beans')
        self.maize_product = Product.objects.create(
            seller=self.seller,
            crop=self.maize,
            title='Fresh Maize Grade A',
            description='New harvest maize',
            unit='kg',
            minimum_order_quantity='10.000',
            location_name='Johannesburg',
            latitude='-26.204100',
            longitude='28.047300',
            expires_at=timezone.now() + timedelta(days=10),
            status=ListingStatus.ACTIVE,
        )
        ProductInventory.objects.create(
            product=self.maize_product,
            available_quantity='500.000',
            reserved_quantity='0.000',
        )
        ProductPricing.objects.create(
            product=self.maize_product,
            currency='USD',
            price='12.00',
            discount='0.00',
            valid_from=timezone.now() - timedelta(days=1),
        )
        self.beans_product = Product.objects.create(
            seller=self.seller,
            crop=self.beans,
            title='Red Beans',
            description='Premium dry beans',
            unit='kg',
            minimum_order_quantity='5.000',
            location_name='Pretoria',
            latitude='-25.747900',
            longitude='28.229300',
            expires_at=timezone.now() + timedelta(days=8),
            status=ListingStatus.ACTIVE,
        )
        ProductInventory.objects.create(
            product=self.beans_product,
            available_quantity='120.000',
            reserved_quantity='0.000',
        )
        ProductPricing.objects.create(
            product=self.beans_product,
            currency='USD',
            price='18.00',
            discount='0.00',
            valid_from=timezone.now() - timedelta(days=1),
        )

    def test_public_search_returns_results_and_logs_query(self):
        """Unauthenticated search should return rows and persist query metadata."""
        response = self.client.get(
            reverse('discovery:search'),
            data={'query': 'maize'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['pagination']['total_count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.maize_product.id)

        log = SearchQueryLog.objects.latest('searched_at')
        self.assertEqual(log.query_text, 'maize')
        self.assertEqual(log.result_count, 1)
        self.assertEqual(log.searched_by, None)

    def test_authenticated_search_logs_actor(self):
        """Authenticated discovery request should store searching user in log."""
        self.client.force_authenticate(user=self.buyer)
        response = self.client.get(reverse('discovery:search'), data={'query': 'beans'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        log = SearchQueryLog.objects.latest('searched_at')
        self.assertEqual(log.searched_by_id, self.buyer.id)

    def test_crop_and_price_filters(self):
        """Crop and price filters should constrain discovery result set."""
        response = self.client.get(
            reverse('discovery:search'),
            data={
                'crop_id': self.maize.id,
                'min_price': '10.00',
                'max_price': '13.00',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['pagination']['total_count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.maize_product.id)

    def test_radius_filter_and_distance_sort(self):
        """Geo radius and distance sort should prioritize nearby listings."""
        far_product = Product.objects.create(
            seller=self.seller,
            crop=self.maize,
            title='Cape Maize',
            description='Far listing',
            unit='kg',
            minimum_order_quantity='4.000',
            location_name='Cape Town',
            latitude='-33.924900',
            longitude='18.424100',
            expires_at=timezone.now() + timedelta(days=7),
            status=ListingStatus.ACTIVE,
        )
        ProductInventory.objects.create(
            product=far_product,
            available_quantity='100.000',
            reserved_quantity='0.000',
        )
        ProductPricing.objects.create(
            product=far_product,
            currency='USD',
            price='11.50',
            discount='0.00',
            valid_from=timezone.now() - timedelta(days=1),
        )

        response = self.client.get(
            reverse('discovery:search'),
            data={
                'latitude': '-26.204100',
                'longitude': '28.047300',
                'radius_km': '80.00',
                'sort': 'distance',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['pagination']['total_count'], 2)
        first = response.data['results'][0]
        self.assertEqual(first['id'], self.maize_product.id)
        self.assertEqual(first['distance_km'], 0.0)

    def test_search_excludes_expired_inactive_and_deleted(self):
        """Discovery should ignore unavailable listings from marketplace state."""
        inactive = Product.objects.create(
            seller=self.seller,
            crop=self.maize,
            title='Inactive Maize',
            description='Hidden listing',
            unit='kg',
            minimum_order_quantity='5.000',
            location_name='Polokwane',
            expires_at=timezone.now() + timedelta(days=6),
            status=ListingStatus.INACTIVE,
        )
        ProductInventory.objects.create(
            product=inactive,
            available_quantity='90.000',
            reserved_quantity='0.000',
        )
        ProductPricing.objects.create(
            product=inactive,
            currency='USD',
            price='9.50',
            discount='0.00',
            valid_from=timezone.now() - timedelta(days=1),
        )
        expired = Product.objects.create(
            seller=self.seller,
            crop=self.maize,
            title='Expired Maize',
            description='Expired listing',
            unit='kg',
            minimum_order_quantity='5.000',
            location_name='Mbombela',
            expires_at=timezone.now() + timedelta(days=1),
            status=ListingStatus.ACTIVE,
        )
        ProductInventory.objects.create(
            product=expired,
            available_quantity='70.000',
            reserved_quantity='0.000',
        )
        ProductPricing.objects.create(
            product=expired,
            currency='USD',
            price='8.50',
            discount='0.00',
            valid_from=timezone.now() - timedelta(days=1),
        )
        deleted = Product.objects.create(
            seller=self.seller,
            crop=self.maize,
            title='Deleted Maize',
            description='Deleted listing',
            unit='kg',
            minimum_order_quantity='5.000',
            location_name='Kimberley',
            expires_at=timezone.now() + timedelta(days=6),
            status=ListingStatus.ACTIVE,
            is_deleted=True,
            deleted_at=timezone.now(),
        )
        ProductInventory.objects.create(
            product=deleted,
            available_quantity='70.000',
            reserved_quantity='0.000',
        )
        ProductPricing.objects.create(
            product=deleted,
            currency='USD',
            price='7.50',
            discount='0.00',
            valid_from=timezone.now() - timedelta(days=1),
        )
        Product.objects.filter(id=expired.id).update(expires_at=timezone.now() - timedelta(minutes=1))

        response = self.client.get(reverse('discovery:search'), data={'query': 'maize'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.maize_product.id, returned_ids)
        self.assertNotIn(inactive.id, returned_ids)
        self.assertNotIn(expired.id, returned_ids)
        self.assertNotIn(deleted.id, returned_ids)
