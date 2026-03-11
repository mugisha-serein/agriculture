"""Discovery workflows for marketplace search, filtering, and weighted ranking."""

from dataclasses import dataclass
from decimal import Decimal
import math

from django.db.models import Q
from django.utils import timezone

from discovery.domain.sorting import DiscoverySort
from discovery.models import SearchQueryLog
from listings.domain.statuses import ListingStatus
from listings.models import Product


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
        """Search available marketplace products and return ranked results."""
        queryset = Product.objects.select_related('crop', 'seller', 'inventory').prefetch_related(
            'pricing'
        ).filter(
            is_deleted=False,
            status=ListingStatus.ACTIVE,
            inventory__available_quantity__gt=0,
            available_from__lte=timezone.localdate(),
            expires_at__gt=timezone.now(),
        )

        if crop_id is not None:
            queryset = queryset.filter(crop_id=crop_id)
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(crop__name__icontains=query)
                | Q(location_name__icontains=query)
            )

        has_location = latitude is not None and longitude is not None
        now = timezone.now()
        tokens = self._tokenize(query)
        ranked_items: list[RankedProduct] = []

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

            score = self._score_product(
                product=product,
                tokens=tokens,
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

    def _score_product(self, *, product, tokens, now, has_location, distance_km):
        """Compute weighted ranking score for discovery relevance."""
        text_score = self._text_score(product=product, tokens=tokens)
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

        if has_location:
            return (
                (0.42 * text_score)
                + (0.28 * distance_score)
                + (0.15 * freshness_score)
                + (0.1 * inventory_score)
                + (0.05 * recency_score)
            )
        return (
            (0.62 * text_score)
            + (0.18 * freshness_score)
            + (0.14 * inventory_score)
            + (0.06 * recency_score)
        )

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
