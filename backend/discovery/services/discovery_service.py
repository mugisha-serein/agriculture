from dataclasses import dataclass
from decimal import Decimal
import math

from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import Q, F, Avg, Count
from django.db.models.functions import Coalesce
from django.utils import timezone

from discovery.domain.sorting import DiscoverySort
from discovery.models import SearchQueryLog, PlatformSystem
from listings.domain.statuses import ListingStatus
from listings.models import Product
from reputation.domain.scoring import DEFAULT_PRIOR_WEIGHT


@dataclass(frozen=True, slots=True)
class RankedProduct:
    """Projection object representing ranked discovery result row."""

    product: Product
    score: float
    distance_km: float | None
    unit_price: Decimal


@dataclass(frozen=True, slots=True)
class DiscoverySearchResult:
    """Paginated discovery search result container."""

    items: list[RankedProduct]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class DiscoveryService:
    """Application service for discovery search and ranking logic."""

    def search_products(
        self,
        *,
        query='',
        crop_id=None,
        min_price=None,
        max_price=None,
        latitude=None,
        longitude=None,
        radius_km=None,
        sort=DiscoverySort.RELEVANCE,
        page=1,
        page_size=20,
        actor=None,
    ):
        """Search available marketplace products using Postgres Full-Text Search."""
        now = timezone.now()
        queryset = Product.objects.select_related('crop', 'seller', 'inventory').prefetch_related(
            'pricing'
        ).annotate(
            seller_avg_rating=Coalesce(Avg('seller__reviews_received__rating', filter=Q(seller__reviews_received__is_visible=True)), 0.0),
            seller_review_count=Count('seller__reviews_received', filter=Q(seller__reviews_received__is_visible=True)),
        ).filter(
            is_deleted=False,
            status=ListingStatus.ACTIVE,
            inventory__available_quantity__gt=0,
            available_from__lte=timezone.localdate(),
            expires_at__gt=now,
        )

        if crop_id is not None:
            queryset = queryset.filter(crop_id=crop_id)

        # Full-text search using Postgres SearchVector
        if query:
            vector = SearchVector('title', weight='A') + \
                     SearchVector('crop__name', weight='A') + \
                     SearchVector('description', weight='B') + \
                     SearchVector('location_name', weight='C')
            search_query = SearchQuery(query)
            queryset = queryset.annotate(
                search_rank=SearchRank(vector, search_query)
            ).filter(search_rank__gt=0.01)

        has_location = latitude is not None and longitude is not None
        tokens = self._tokenize(query)
        ranked_items: list[RankedProduct] = []

        # Calculate average prices per crop for competitiveness
        # We use a subquery/aggregation on the filtered queryset
        crop_avg_prices = {
            row['crop_id']: float(row['avg_price'] or 0.0)
            for row in Product.objects.filter(id__in=queryset.values('id')).annotate(
                active_price=F('pricing__price') # Simplified for avg calculation
            ).values('crop_id').annotate(avg_price=Avg('active_price'))
        }

        global_mean_rating = self._global_average_rating()

        for product in queryset:
            distance_km = None
            if has_location:
                if product.latitude is None or product.longitude is None:
                    if radius_km is not None or sort == DiscoverySort.DISTANCE:
                        continue
                else:
                    distance_km = self._distance_km(
                        latitude=float(latitude),
                        longitude=float(longitude),
                        target_latitude=float(product.latitude),
                        target_longitude=float(product.longitude),
                    )
                    if radius_km is not None and distance_km > float(radius_km):
                        continue

            pricing = product.get_active_pricing(now=now)
            if pricing is None:
                continue
            unit_price = pricing.price - pricing.discount
            if unit_price <= 0:
                continue
            if min_price is not None and unit_price < min_price:
                continue
            if max_price is not None and unit_price > max_price:
                continue

            # Combine manual scoring with Postgres SearchRank if available
            text_score = getattr(product, 'search_rank', 0.0) if query else self._text_score(product=product, tokens=tokens)
            
            # Reputation score
            reputation_score = self._bayesian_score(
                average_rating=float(product.seller_avg_rating),
                review_count=int(product.seller_review_count),
                global_mean=global_mean_rating,
                prior_weight=float(DEFAULT_PRIOR_WEIGHT)
            ) / 5.0 # Normalize to 0-1

            # Price competitiveness
            avg_price = crop_avg_prices.get(product.crop_id, float(unit_price))
            price_comp_score = 1.0 - min(1.0, float(unit_price) / avg_price) if avg_price > 0 else 0.5
            # We want better prices to have higher scores, so 1.0 - ratio is a good start, but let's cap it
            price_comp_score = max(0.0, min(1.0, price_comp_score + 0.5))

            score = self._score_product(
                product=product,
                text_score=float(text_score),
                reputation_score=reputation_score,
                price_comp_score=price_comp_score,
                now=now,
                has_location=has_location,
                distance_km=distance_km,
            )
            ranked_items.append(
                RankedProduct(
                    product=product,
                    score=score,
                    distance_km=distance_km,
                    unit_price=unit_price,
                )
            )

        ranked_items = self._sort_ranked_items(ranked_items=ranked_items, sort=sort, has_location=has_location)

        total_count = len(ranked_items)
        total_pages = max(1, math.ceil(total_count / page_size))
        clamped_page = min(max(page, 1), total_pages)
        start = (clamped_page - 1) * page_size
        end = start + page_size
        paged_items = ranked_items[start:end]

        self._log_search(
            actor=actor,
            query=query,
            crop_id=crop_id,
            min_price=min_price,
            max_price=max_price,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            sort=sort,
            page=clamped_page,
            page_size=page_size,
            result_count=total_count,
        )
        return DiscoverySearchResult(
            items=paged_items,
            total_count=total_count,
            page=clamped_page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def search_systems(self, query=''):
        """Search platform systems using Postgres Full-Text Search."""
        queryset = PlatformSystem.objects.filter(is_active=True)
        if query:
            vector = SearchVector('name', weight='A') + SearchVector('description', weight='B')
            search_query = SearchQuery(query)
            queryset = queryset.annotate(
                rank=SearchRank(vector, search_query)
            ).filter(rank__gt=0.01).order_by('-rank', 'position')
        else:
            queryset = queryset.order_by('position')
        
        return queryset

    def _sort_ranked_items(self, *, ranked_items, sort, has_location):
        """Sort ranked items according to requested strategy."""
        if sort == DiscoverySort.PRICE_ASC:
            return sorted(ranked_items, key=lambda item: (item.unit_price, -item.score))
        if sort == DiscoverySort.PRICE_DESC:
            return sorted(ranked_items, key=lambda item: (-item.unit_price, -item.score))
        if sort == DiscoverySort.NEWEST:
            return sorted(ranked_items, key=lambda item: (-item.product.created_at.timestamp(), -item.score))
        if sort == DiscoverySort.DISTANCE and has_location:
            return sorted(
                ranked_items,
                key=lambda item: (
                    float('inf') if item.distance_km is None else item.distance_km,
                    -item.score,
                ),
            )
        return sorted(
            ranked_items,
            key=lambda item: (-item.score, -item.product.created_at.timestamp()),
        )

    def _score_product(self, *, product, text_score, reputation_score, price_comp_score, now, has_location, distance_km):
        """Compute weighted ranking score for discovery relevance."""
        distance_score = 0.0
        if has_location and distance_km is not None:
            distance_score = 1 / (1 + distance_km)

        lifespan_seconds = 60 * 60 * 24 * 30
        freshness_score = max(
            0.0,
            min(1.0, (product.expires_at - now).total_seconds() / lifespan_seconds),
        )

        inventory_value = float(product.inventory.available_quantity) if product.inventory else 0.0
        min_qty_value = max(float(product.minimum_order_quantity), 1.0)
        inventory_score = min(1.0, math.log10(inventory_value + 1) / math.log10(min_qty_value * 25 + 1))

        age_seconds = max((now - product.created_at).total_seconds(), 0.0)
        recency_score = max(0.0, 1 - min(age_seconds / lifespan_seconds, 1.0))

        # Weighting
        # relevance (text_score)
        # seller_reputation_weight (reputation_score)
        # freshness_weight (freshness_score)
        # distance_weight (distance_score)
        # price_competitiveness (price_comp_score)

        if has_location:
            return (
                (0.35 * text_score)
                + (0.25 * reputation_score)
                + (0.15 * freshness_score)
                + (0.15 * distance_score)
                + (0.10 * price_comp_score)
            )
        return (
            (0.40 * text_score)
            + (0.30 * reputation_score)
            + (0.15 * freshness_score)
            + (0.15 * price_comp_score)
        )

    def _bayesian_score(self, *, average_rating, review_count, global_mean, prior_weight):
        """Compute Bayesian adjusted rating score."""
        reviews_weight = float(review_count)
        prior = float(prior_weight)
        if reviews_weight + prior <= 0:
            return float(global_mean)
        return ((reviews_weight / (reviews_weight + prior)) * average_rating) + (
            (prior / (reviews_weight + prior)) * global_mean
        )

    def _global_average_rating(self):
        """Return global mean rating over all visible reviews."""
        # Using a default or calculating from actual reviews
        from reputation.models import Review
        value = Review.objects.filter(is_visible=True).aggregate(avg=Avg('rating'))['avg']
        if value is None:
            return 3.5 # Default midpoint
        return float(value)

    def _text_score(self, *, product, tokens):
        """Compute normalized text match score from query tokens."""
        if not tokens:
            return 0.6
        title = product.title.lower()
        description = product.description.lower()
        crop_name = product.crop.name.lower()
        location_name = product.location_name.lower()
        token_scores = []
        for token in tokens:
            token_score = 0.0
            if token in title:
                token_score += 1.0
            if token in crop_name:
                token_score += 0.85
            if token in description:
                token_score += 0.55
            if token in location_name:
                token_score += 0.3
            token_scores.append(min(1.0, token_score))
        return sum(token_scores) / len(token_scores)

    def _tokenize(self, query):
        """Split query into lowercase searchable tokens."""
        return [part.strip().lower() for part in query.split() if part.strip()]

    def _log_search(
        self,
        *,
        actor,
        query,
        crop_id,
        min_price,
        max_price,
        latitude,
        longitude,
        radius_km,
        sort,
        page,
        page_size,
        result_count,
    ):
        """Persist search metadata for analytics and auditability."""
        SearchQueryLog.objects.create(
            searched_by=actor if getattr(actor, 'is_authenticated', False) else None,
            query_text=query,
            filters={
                'crop_id': crop_id,
                'min_price': str(min_price) if isinstance(min_price, Decimal) else min_price,
                'max_price': str(max_price) if isinstance(max_price, Decimal) else max_price,
            },
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            sort_by=sort,
            page=page,
            page_size=page_size,
            result_count=result_count,
            searched_at=timezone.now(),
        )

    def _distance_km(self, *, latitude, longitude, target_latitude, target_longitude):
        """Calculate great-circle distance between two points in kilometers."""
        radius = 6371.0
        lat1 = math.radians(latitude)
        lon1 = math.radians(longitude)
        lat2 = math.radians(target_latitude)
        lon2 = math.radians(target_longitude)
        delta_lat = lat2 - lat1
        delta_lon = lon2 - lon1
        a_value = (
            (math.sin(delta_lat / 2) ** 2)
            + (math.cos(lat1) * math.cos(lat2) * (math.sin(delta_lon / 2) ** 2))
        )
        c_value = 2 * math.atan2(math.sqrt(a_value), math.sqrt(1 - a_value))
        return radius * c_value
