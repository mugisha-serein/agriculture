"""Reputation app API tests."""

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from listings.domain.statuses import ListingStatus
from listings.models import Crop, Product, ProductInventory, ProductPricing
from logistics.models import Shipment
from orders.models import Order
from orders.models import OrderItem
from reputation.models import Review
from users.models import User


class ReputationApiTests(APITestCase):
    """End-to-end tests for reputation review and scoring workflows."""

    def setUp(self):
        """Create completed order participant fixtures for review tests."""
        self.buyer = User.objects.create_user(
            email='buyer@example.com',
            first_name='Buyer',
            last_name='One',
            password='StrongPass123',
            role='buyer',
            is_active=True,
        )
        self.seller = User.objects.create_user(
            email='seller@example.com',
            first_name='Seller',
            last_name='One',
            password='StrongPass123',
            role='seller',
            is_active=True,
        )
        self.seller_two = User.objects.create_user(
            email='seller2@example.com',
            first_name='Seller',
            last_name='Two',
            password='StrongPass123',
            role='seller',
            is_active=True,
        )
        self.transporter = User.objects.create_user(
            email='transporter@example.com',
            first_name='Transporter',
            last_name='One',
            password='StrongPass123',
            role='transporter',
            is_active=True,
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            first_name='Other',
            last_name='User',
            password='StrongPass123',
            role='buyer',
            is_active=True,
        )
        self.crop = Crop.objects.create(name='Spinach', slug='spinach')
        self.product = Product.objects.create(
            seller=self.seller,
            crop=self.crop,
            title='Fresh Spinach',
            unit='kg',
            minimum_order_quantity='2.000',
            location_name='Durban',
            expires_at=timezone.now() + timedelta(days=10),
            status=ListingStatus.ACTIVE,
        )
        ProductInventory.objects.create(
            product=self.product,
            available_quantity='500.000',
            reserved_quantity='0.000',
        )
        ProductPricing.objects.create(
            product=self.product,
            currency='USD',
            price='5.00',
            discount='0.00',
            valid_from=timezone.now() - timedelta(days=1),
        )
        self.order = Order.objects.create(
            order_number='ORD-REP-0001',
            buyer=self.buyer,
            status='completed',
            currency='ZAR',
            subtotal_amount='50.00',
            seller_count=1,
            item_count=1,
            placed_at=timezone.now(),
            confirmed_at=timezone.now(),
            completed_at=timezone.now(),
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            seller=self.seller,
            product_title=self.product.title,
            unit=self.product.unit,
            unit_price='5.00',
            quantity='10.000',
            line_total='50.00',
            status='fulfilled',
            allocated_at=timezone.now(),
            fulfilled_at=timezone.now(),
        )
        Shipment.objects.create(
            shipment_reference='SHP-REP-0001',
            tracking_code='TRKREP000001',
            order=self.order,
            seller=self.seller,
            buyer=self.buyer,
            transporter=self.transporter,
            status='delivered',
            pickup_address='Farm 9',
            delivery_address='Market 1',
            assigned_at=timezone.now(),
            picked_up_at=timezone.now(),
            in_transit_at=timezone.now(),
            delivered_at=timezone.now(),
        )

    def test_participant_can_create_review(self):
        """Order participant can create review for another participant."""
        self.client.force_authenticate(user=self.buyer)
        response = self.client.post(
            reverse('reputation:create-review'),
            data={
                'order_id': self.order.id,
                'reviewee_id': self.seller.id,
                'rating': 5,
                'comment': 'Excellent seller',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['rating'], 5)
        self.assertEqual(Review.objects.count(), 1)

    def test_duplicate_review_is_blocked(self):
        """Duplicate order review from same reviewer to same reviewee should fail."""
        self.client.force_authenticate(user=self.buyer)
        payload = {
            'order_id': self.order.id,
            'reviewee_id': self.seller.id,
            'rating': 4,
            'comment': 'Good service',
        }
        first = self.client.post(reverse('reputation:create-review'), data=payload, format='json')
        second = self.client.post(reverse('reputation:create-review'), data=payload, format='json')
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_completed_order_review_is_blocked(self):
        """Reviews should be blocked when order status is not completed."""
        pending_order = Order.objects.create(
            order_number='ORD-REP-0002',
            buyer=self.buyer,
            status='pending',
            currency='ZAR',
            subtotal_amount='20.00',
            seller_count=1,
            item_count=1,
            placed_at=timezone.now(),
        )
        OrderItem.objects.create(
            order=pending_order,
            product=self.product,
            seller=self.seller,
            product_title=self.product.title,
            unit=self.product.unit,
            unit_price='5.00',
            quantity='4.000',
            line_total='20.00',
            status='allocated',
            allocated_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.buyer)
        response = self.client.post(
            reverse('reputation:create-review'),
            data={
                'order_id': pending_order.id,
                'reviewee_id': self.seller.id,
                'rating': 4,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_summary_and_leaderboard_bayesian_scoring(self):
        """Summary and leaderboard should expose Bayesian-adjusted scores."""
        self.client.force_authenticate(user=self.buyer)
        self.client.post(
            reverse('reputation:create-review'),
            data={'order_id': self.order.id, 'reviewee_id': self.seller.id, 'rating': 5},
            format='json',
        )

        second_order = Order.objects.create(
            order_number='ORD-REP-0003',
            buyer=self.other_user,
            status='completed',
            currency='ZAR',
            subtotal_amount='30.00',
            seller_count=1,
            item_count=1,
            placed_at=timezone.now(),
            confirmed_at=timezone.now(),
            completed_at=timezone.now(),
        )
        OrderItem.objects.create(
            order=second_order,
            product=self.product,
            seller=self.seller_two,
            product_title=self.product.title,
            unit=self.product.unit,
            unit_price='5.00',
            quantity='6.000',
            line_total='30.00',
            status='fulfilled',
            allocated_at=timezone.now(),
            fulfilled_at=timezone.now(),
        )
        self.client.force_authenticate(user=self.other_user)
        self.client.post(
            reverse('reputation:create-review'),
            data={'order_id': second_order.id, 'reviewee_id': self.seller_two.id, 'rating': 3},
            format='json',
        )

        summary = self.client.get(reverse('reputation:user-summary', kwargs={'user_id': self.seller.id}))
        self.assertEqual(summary.status_code, status.HTTP_200_OK)
        self.assertEqual(summary.data['review_count'], 1)
        self.assertGreater(summary.data['bayesian_score'], 0)

        leaderboard = self.client.get(
            reverse('reputation:leaderboard'),
            data={'role': 'seller', 'limit': 10},
        )
        self.assertEqual(leaderboard.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(leaderboard.data['results']), 2)
        first = leaderboard.data['results'][0]
        self.assertEqual(first['role'], 'seller')
        self.assertEqual(first['user_id'], self.seller.id)

    def test_non_participant_cannot_review_order(self):
        """User not involved in order cannot create review."""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(
            reverse('reputation:create-review'),
            data={
                'order_id': self.order.id,
                'reviewee_id': self.seller.id,
                'rating': 4,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_review_helpfulness_votes_influence_summary(self):
        """Helpfulness votes should show up in the summary trust signals."""
        self.client.force_authenticate(user=self.buyer)
        self.client.post(
            reverse('reputation:create-review'),
            data={
                'order_id': self.order.id,
                'reviewee_id': self.seller.id,
                'rating': 5,
            },
            format='json',
        )
        review = Review.objects.get(order=self.order, reviewer=self.buyer)
        self.client.force_authenticate(user=self.other_user)
        vote = self.client.post(
            reverse('reputation:review-vote'),
            data={'review_id': review.id, 'is_helpful': True},
            format='json',
        )
        self.assertEqual(vote.status_code, status.HTTP_200_OK)
        summary = self.client.get(reverse('reputation:user-summary', kwargs={'user_id': self.seller.id}))
        self.assertGreater(summary.data['review_helpfulness'], 0)
        self.assertIn('Helpful Reviews', [badge['name'] for badge in summary.data['badges']])

    def test_flagging_review_hides_manipulated_reviews(self):
        """Multiple flags should hide a review and adjust summary."""
        self.client.force_authenticate(user=self.buyer)
        self.client.post(
            reverse('reputation:create-review'),
            data={
                'order_id': self.order.id,
                'reviewee_id': self.seller.id,
                'rating': 5,
            },
            format='json',
        )
        review = Review.objects.get(order=self.order, reviewer=self.buyer)
        flaggers = [self.seller, self.other_user, self.transporter]
        for flagger in flaggers:
            self.client.force_authenticate(user=flagger)
            response = self.client.post(
                reverse('reputation:review-flag'),
                data={'review_id': review.id, 'reason': 'Suspicious content'},
                format='json',
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        review.refresh_from_db()
        self.assertFalse(review.is_visible)

    def test_badges_exposed_via_summary(self):
        """Summary should include badges when trust signals are high."""
        self.client.force_authenticate(user=self.buyer)
        self.client.post(
            reverse('reputation:create-review'),
            data={
                'order_id': self.order.id,
                'reviewee_id': self.seller.id,
                'rating': 5,
            },
            format='json',
        )
        review = Review.objects.get(order=self.order, reviewer=self.buyer)
        self.client.force_authenticate(user=self.other_user)
        self.client.post(
            reverse('reputation:review-vote'),
            data={'review_id': review.id, 'is_helpful': True},
            format='json',
        )
        summary = self.client.get(reverse('reputation:user-summary', kwargs={'user_id': self.seller.id}))
        self.assertIn('Helpful Reviews', [badge['name'] for badge in summary.data['badges']])
