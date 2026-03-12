"""API views for discovery search workflows."""

from django.db.models import Avg, Count, Q
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from discovery.api.serializers import DiscoveryProductSerializer, DiscoverySearchSerializer, PlatformSystemSerializer
from discovery.services.discovery_service import DiscoveryService
from discovery.services.recommendation_service import RecommendationService
from discovery.models import PlatformSystem
from listings.api.serializers import ProductSerializer
from listings.domain.statuses import ListingStatus
from listings.models import Crop, Product
from users.models import User


class SearchView(APIView):
    """Search available marketplace listings with ranking."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Handle discovery search query requests."""
        serializer = DiscoverySearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        service = DiscoveryService()
        result = service.search_products(
            actor=request.user if request.user.is_authenticated else None,
            **serializer.validated_data,
        )
        items = []
        for ranked in result.items:
            items.append(
                {
                    'id': ranked.product.id,
                    'title': ranked.product.title,
                    'description': ranked.product.description,
                    'crop_id': ranked.product.crop_id,
                    'crop_name': ranked.product.crop.name,
                    'seller_id': ranked.product.seller_id,
                    'seller_email': ranked.product.seller.email,
                    'unit': ranked.product.unit,
                    'price_per_unit': ranked.unit_price,
                    'quantity_available': (
                        ranked.product.inventory.available_quantity
                        if ranked.product.inventory
                        else 0
                    ),
                    'minimum_order_quantity': ranked.product.minimum_order_quantity,
                    'location_name': ranked.product.location_name,
                    'latitude': ranked.product.latitude,
                    'longitude': ranked.product.longitude,
                    'expires_at': ranked.product.expires_at,
                    'score': round(ranked.score, 6),
                    'distance_km': None
                    if ranked.distance_km is None
                    else round(ranked.distance_km, 3),
                }
            )
        payload = {
            'results': DiscoveryProductSerializer(items, many=True).data,
            'systems': PlatformSystemSerializer(service.search_systems(query=serializer.validated_data.get('query', '')), many=True).data,
            'pagination': {
                'total_count': result.total_count,
                'page': result.page,
                'page_size': result.page_size,
                'total_pages': result.total_pages,
            },
        }
        return Response(payload, status=status.HTTP_200_OK)


class HomeView(APIView):
    """Serve landing page content for buyer-facing home page."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        now = timezone.now()
        today = timezone.localdate()

        available_products = Product.objects.select_related('crop', 'seller', 'inventory').filter(
            is_deleted=False,
            status=ListingStatus.ACTIVE,
            inventory__available_quantity__gt=0,
            available_from__lte=today,
            expires_at__gt=now,
            seller__is_verified=True,
            seller__is_active=True,
        ).order_by('-created_at')

        featured_products = ProductSerializer(available_products[:6], many=True).data

        total_crops = Crop.objects.filter(is_active=True).count()
        total_products = available_products.count()
        verified_sellers = User.objects.filter(role='seller', is_verified=True, is_active=True).count()
        verified_transporters = User.objects.filter(role='transporter', is_verified=True, is_active=True).count()

        systems = PlatformSystem.objects.filter(is_active=True).order_by('position')
        system_cards = PlatformSystemSerializer(systems, many=True).data

        payload = {
            'hero': {
                'title': 'Grow Your Future.',
                'subtitle': (
                    'The transparent marketplace for agricultural produce, connecting farmers and buyers with '
                    'verified logistics.'
                ),
                'primary_cta_label': 'Explore Marketplace',
                'primary_cta_href': '/discovery',
                'secondary_cta_label': 'Join as Seller',
                'secondary_cta_href': '/register',
            },
            'banner': {
                'kicker': 'System Coverage',
                'title': 'All the tools you need, in one place.',
                'subtitle': (
                    'Discover, list, sell, ship, and get paid with verified participants across the full supply chain.'
                ),
                'cards': system_cards,
            },
            'slideshow': {
                'slides': [
                    {
                        'title': 'Everything You Need in One System',
                        'description': 'Listings, escrow, logistics, and reputation are built in and verified.',
                    },
                    {
                        'title': 'Verified Sellers & Transporters',
                        'description': 'Every listing and shipment is powered by verified partners.',
                    },
                    {
                        'title': 'Live Shipment Visibility',
                        'description': 'Track origin-to-destination updates without leaving the platform.',
                    },
                ],
                'aside': {
                    'title': 'Verified Network',
                    'description': 'Every seller and transporter is verified before going live.',
                    'metric_label': 'Verified partners',
                    'metric_value': verified_sellers + verified_transporters,
                },
            },
            'stats': {
                'total_crops': total_crops,
                'total_products': total_products,
                'verified_sellers': verified_sellers,
                'verified_transporters': verified_transporters,
            },
            'featured': {
                'title': 'Featured Products',
                'subtitle': 'Curated listings from verified sellers across the region.',
                'cta_label': 'View More',
                'cta_href': '/discovery',
                'item_cta_label': 'View Listing',
            },
            'featured_products': featured_products,
            'verified': {
                'title': 'Verified Sellers & Transporters',
                'subtitle': 'Trust-backed participants ready to fulfill orders end-to-end.',
                'sellers_label': 'Verified Sellers',
                'transporters_label': 'Verified Transporters',
            },
            'verified_sellers': self._top_verified_users(role='seller', limit=3),
            'verified_transporters': self._top_verified_users(role='transporter', limit=3),
            'how_it_works': {
                'title': 'How it Works',
                'subtitle': 'A modular ecosystem for secure agricultural trade.',
                'steps': [
                    {
                        'title': 'List Produce',
                        'description': (
                            'Sellers list crops with detailed specifications. Our discovery engine ensures maximum '
                            'visibility.'
                        ),
                        'icon': 'shovel',
                        'tone': 'accent',
                    },
                    {
                        'title': 'Secure Escrow',
                        'description': (
                            'Payments are held in immutable escrow transactions until delivery is confirmed by both '
                            'parties.'
                        ),
                        'icon': 'shield',
                        'tone': 'primary',
                    },
                    {
                        'title': 'Verified Logistics',
                        'description': (
                            'Integrated shipment tracking and coordination with verified transporters for every order.'
                        ),
                        'icon': 'truck',
                        'tone': 'secondary',
                    },
                ],
            },
            'empty_state': {
                'featured_products': 'No featured listings are available yet.',
                'verified_sellers': 'Verified sellers will appear once approved.',
                'verified_transporters': 'Verified transporters will appear once approved.',
            },
        }

        return Response(payload, status=status.HTTP_200_OK)

    @staticmethod
    def _top_verified_users(*, role, limit):
        users = (
            User.objects.filter(role=role, is_verified=True, is_active=True)
            .annotate(
                review_count=Count(
                    'reviews_received',
                    filter=Q(reviews_received__is_visible=True),
                ),
                average_rating=Coalesce(
                    Avg('reviews_received__rating', filter=Q(reviews_received__is_visible=True)),
                    0.0,
                ),
            )
            .order_by('-average_rating', '-review_count', 'id')[:limit]
        )

        results = []
        for user in users:
            full_name = f"{user.first_name} {user.last_name}".strip() or user.email
            review_count = int(getattr(user, 'review_count', 0) or 0)
            average_rating = float(getattr(user, 'average_rating', 0.0) or 0.0)
            rating_label = 'New' if review_count == 0 else f'{average_rating:.1f}'
            review_label = f'{review_count} review' + ('s' if review_count != 1 else '')

            results.append(
                {
                    'user_id': user.id,
                    'display_name': full_name,
                    'email': user.email,
                    'role': user.role,
                    'review_count': review_count,
                    'average_rating': round(average_rating, 2),
                    'rating_label': rating_label,
                    'review_label': review_label,
                }
            )

        return results


class RecommendedProductsView(APIView):
    """Personalized product recommendations for the authenticated user."""

    permission_classes = [permissions.AllowAny] # Service handles guest fallback

    def get(self, request):
        """Handle recommendation requests with optional coordinates."""
        service = RecommendationService()
        latitude = request.query_params.get('latitude')
        longitude = request.query_params.get('longitude')
        limit = int(request.query_params.get('limit', 10))

        recommendations = service.get_recommendations(
            user=request.user,
            latitude=latitude,
            longitude=longitude,
            limit=limit,
        )

        items = []
        for rec in recommendations:
            product = rec['product']
            now = timezone.now()
            pricing = product.get_active_pricing(now=now)
            unit_price = (pricing.price - pricing.discount) if pricing else 0

            items.append(
                {
                    'id': product.id,
                    'title': product.title,
                    'description': product.description,
                    'crop_id': product.crop_id,
                    'crop_name': product.crop.name,
                    'seller_id': product.seller_id,
                    'seller_email': product.seller.email,
                    'unit': product.unit,
                    'price_per_unit': unit_price,
                    'quantity_available': (
                        product.inventory.available_quantity
                        if product.inventory
                        else 0
                    ),
                    'minimum_order_quantity': product.minimum_order_quantity,
                    'location_name': product.location_name,
                    'latitude': product.latitude,
                    'longitude': product.longitude,
                    'expires_at': product.expires_at,
                    'score': round(rec['score'], 6),
                    'distance_km': None
                    if rec['distance_km'] is None
                    else round(rec['distance_km'], 3),
                }
            )

        return Response(
            {
                'results': DiscoveryProductSerializer(items, many=True).data,
                'count': len(items),
            },
            status=status.HTTP_200_OK,
        )
