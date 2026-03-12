from datetime import timedelta
import math
import re

from django.db.models import Count, Q, Avg
from django.db.models.functions import Coalesce
from django.utils import timezone

from audit.models import AuditRequestAction
from discovery.models import SearchQueryLog
from discovery.services.discovery_service import DiscoveryService
from listings.domain.statuses import ListingStatus
from listings.models import Product, Crop
from orders.models import OrderItem


class RecommendationService:
    """Service to generate personalized product recommendations."""

    def __init__(self):
        self.discovery_service = DiscoveryService()

    def get_recommendations(self, *, user, latitude=None, longitude=None, limit=10):
        """Fetch personalized product recommendations for a user."""
        if not user or not user.is_authenticated:
            # Fallback to general popular/seasonal products if unauthenticated
            return self._get_fallback_recommendations(latitude, longitude, limit)

        # 1. Gather User Preferences from History
        interested_crop_ids = self._get_interested_crops(user)
        
        # 2. Extract context (Location & Time)
        effective_lat, effective_lon = self._get_effective_location(user, latitude, longitude)
        now = timezone.now()
        current_month = now.month

        # 3. Build Base Queryset
        queryset = Product.objects.select_related('crop', 'seller', 'inventory').prefetch_related(
            'pricing'
        ).filter(
            is_deleted=False,
            status=ListingStatus.ACTIVE,
            inventory__available_quantity__gt=0,
            available_from__lte=timezone.localdate(),
            expires_at__gt=now,
        ).exclude(seller=user) # Don't recommend own products

        # 4. Filter by interested crops if any
        if interested_crop_ids:
            # We don't strictly filter, we'll boost them in scoring later or prioritze them
            # For performance, let's include products from these crops + others
            pass

        # 5. Scoring and Ranking
        # Since we're doing complex scoring, we'll iterate and score 
        # (similar to discovery service but with personalization)
        
        global_mean_rating = self.discovery_service._global_average_rating()
        
        # Annotate with reputation data
        queryset = queryset.annotate(
            seller_avg_rating=Coalesce(Avg('seller__reviews_received__rating', filter=Q(seller__reviews_received__is_visible=True)), 0.0),
            seller_review_count=Count('seller__reviews_received', filter=Q(seller__reviews_received__is_visible=True)),
        )

        # Optimization: and only fetch a reasonable candidate pool
        # For a real recommendation engine, this would be a vector search or precomputed set
        candidate_pool = queryset.order_by('-created_at')[:200]

        scored_items = []
        for product in candidate_pool:
            # Relevance (Personalization)
            personal_relevance = 1.0 if product.crop_id in interested_crop_ids else 0.0
            
            # Distance
            distance_km = None
            if effective_lat and effective_lon and product.latitude and product.longitude:
                distance_km = self.discovery_service._distance_km(
                    latitude=float(effective_lat),
                    longitude=float(effective_lon),
                    target_latitude=float(product.latitude),
                    target_longitude=float(product.longitude),
                )
            
            # Reputation
            reputation_score = self.discovery_service._bayesian_score(
                average_rating=float(product.seller_avg_rating),
                review_count=int(product.seller_review_count),
                global_mean=global_mean_rating,
                prior_weight=3.0 # Assuming prior weight
            ) / 5.0

            # Seasonality
            # available_from month relative to current month
            available_month = product.available_from.month
            seasonality_score = 1.0 if available_month == current_month else (
                0.8 if available_month == (current_month % 12 + 1) else 0.3
            )

            # Combined Score
            # personalize higher
            final_score = (
                (0.40 * personal_relevance) +
                (0.20 * seasonality_score) +
                (0.20 * reputation_score) +
                (0.20 * (1 / (1 + distance_km) if distance_km is not None else 0.5))
            )

            scored_items.append({
                'product': product,
                'score': final_score,
                'distance_km': distance_km
            })

        # Sort and Limit
        scored_items.sort(key=lambda x: x['score'], reverse=True)
        return scored_items[:limit]

    def _get_interested_crops(self, user):
        """Identify crop IDs the user has interacted with (views/purchases)."""
        interested = set()
        
        # Purchase History
        purchased_crops = OrderItem.objects.filter(
            order__buyer=user
        ).values_list('product__crop_id', flat=True).distinct()
        interested.update(purchased_crops)

        # View History (Audit Logs)
        # Endpoint: /api/marketplace/products/<id>/
        view_logs = AuditRequestAction.objects.filter(
            actor=user,
            app_scope='marketplace',
            action_name='product-detail', # Assuming this is the name or we parse path
            status_code=200
        ).values_list('request_path', flat=True)[:100]

        for path in view_logs:
            match = re.search(r'/products/(\d+)/', path)
            if match:
                product_id = int(match.group(1))
                # For efficiency, we could pre-fetch these or cache them
                # Here we just look for unique ones
                try:
                    product = Product.objects.get(id=product_id)
                    interested.add(product.crop_id)
                except Product.DoesNotExist:
                    continue

        return interested

    def _get_effective_location(self, user, latitude, longitude):
        """Determine most likely location for the user."""
        if latitude and longitude:
            return latitude, longitude
        
        # Fallback to last search log
        last_search = SearchQueryLog.objects.filter(searched_by=user, latitude__isnull=False).order_by('-searched_at').first()
        if last_search:
            return last_search.latitude, last_search.longitude
        
        return None, None

    def _get_fallback_recommendations(self, latitude, longitude, limit):
        """Generic recommendations for guests based on location/season."""
        # Just seasonal products near location if possible
        now = timezone.now()
        queryset = Product.objects.select_related('crop', 'seller', 'inventory').prefetch_related(
            'pricing'
        ).filter(
            is_deleted=False,
            status=ListingStatus.ACTIVE,
            inventory__available_quantity__gt=0,
            available_from__lte=timezone.localdate(),
            expires_at__gt=now,
        ).order_by('-created_at')[:limit]
        
        return [{'product': p, 'score': 0.5, 'distance_km': None} for p in queryset]
