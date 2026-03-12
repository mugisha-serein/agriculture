import uuid
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from audit.models import AuditRequestAction
from listings.domain.statuses import ListingStatus
from listings.models import Crop, Product, ProductInventory, ProductPricing
from orders.models import Order, OrderItem
from users.models import User


class RecommendationTests(APITestCase):
    """Tests for personalized product recommendations."""

    def setUp(self):
        """Create fixtures for recommendation tests."""
        self.seller = User.objects.create_user(
            email='seller@example.com',
            first_name='Seller',
            last_name='One',
            password='StrongPass123',
            role='seller',
            is_active=True,
        )
        self.buyer = User.objects.create_user(
            email='buyer@example.com',
            first_name='Buyer',
            last_name='One',
            password='StrongPass123',
            role='buyer',
            is_active=True,
        )
        self.maize = Crop.objects.create(name='Maize', slug='maize')
        self.beans = Crop.objects.create(name='Beans', slug='beans')
        self.wheat = Crop.objects.create(name='Wheat', slug='wheat')

        # Maize products
        self.maize_prod = self._create_product('Maize A', self.maize)
        self.maize_prod_2 = self._create_product('Maize B', self.maize)
        
        # Beans product
        self.beans_prod = self._create_product('Beans A', self.beans)
        
        # Wheat product
        self.wheat_prod = self._create_product('Wheat A', self.wheat)

    def _create_product(self, title, crop):
        product = Product.objects.create(
            seller=self.seller,
            crop=crop,
            title=title,
            description=f'Description for {title}',
            unit='kg',
            expires_at=timezone.now() + timedelta(days=10),
            status=ListingStatus.ACTIVE,
            location_name='Johannesburg',
            latitude='-26.204100',
            longitude='28.047300',
        )
        ProductInventory.objects.create(product=product, available_quantity=100)
        ProductPricing.objects.create(product=product, price='10.00')
        return product

    def test_guest_gets_fallback_recommendations(self):
        """Unauthenticated users should see latest products."""
        response = self.client.get(reverse('discovery:recommendations'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreater(len(response.data['results']), 0)

    def test_recommendations_based_on_view_history(self):
        """Users should see products from crops they've recently viewed."""
        self.client.force_authenticate(user=self.buyer)
        
        # Simulate viewing maize products via audit logs
        AuditRequestAction.objects.create(
            actor=self.buyer,
            app_scope='marketplace',
            action_name='product-detail',
            request_path=f'/api/marketplace/products/{self.maize_prod.id}/',
            status_code=200,
            event_hash=str(uuid.uuid4())
        )

        response = self.client.get(reverse('discovery:recommendations'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # High score should be for Maize products
        first_result = response.data['results'][0]
        self.assertEqual(first_result['crop_id'], self.maize.id)

    def test_recommendations_based_on_purchase_history(self):
        """Users should see products from crops they've previously purchased."""
        self.client.force_authenticate(user=self.buyer)
        
        # Simulate purchase of beans
        order = Order.objects.create(order_number='ORD-REC-1', buyer=self.buyer, status='COMPLETED')
        OrderItem.objects.create(
            order=order,
            product=self.beans_prod,
            seller=self.seller,
            product_title='Beans A',
            unit='kg',
            unit_price=10.0,
            quantity=1.0,
            line_total=10.0
        )

        response = self.client.get(reverse('discovery:recommendations'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Top result should be related to Beans
        first_result = response.data['results'][0]
        self.assertEqual(first_result['crop_id'], self.beans.id)

    def test_recommendations_near_location(self):
        """Product scores should be influenced by proximity."""
        self.client.force_authenticate(user=self.buyer)
        
        # Create a far product
        far_wheat = Product.objects.create(
            seller=self.seller,
            crop=self.wheat,
            title='Far Wheat',
            description='Wheat far away',
            unit='kg',
            expires_at=timezone.now() + timedelta(days=10),
            status=ListingStatus.ACTIVE,
            location_name='Cape Town',
            latitude='-33.924900',
            longitude='18.424100',
        )
        ProductInventory.objects.create(product=far_wheat, available_quantity=100)
        ProductPricing.objects.create(product=far_wheat, price='10.00')

        # Local wheat ( Johannesburg)
        local_wheat = self.wheat_prod

        # Ask for recommendations near Johannesburg
        response = self.client.get(reverse('discovery:recommendations'), data={
            'latitude': '-26.204100',
            'longitude': '28.047300'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = response.data['results']
        ids = [item['id'] for item in results]
        
        # Local wheat should rank higher than far wheat if other factors are equal
        self.assertLess(ids.index(local_wheat.id), ids.index(far_wheat.id))
