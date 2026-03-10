"""API views for marketplace crop and product operations."""

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsVerifiedRole
from listings.api.permissions import IsSellerOrAdmin
from listings.api.serializers import CropCreateSerializer, CropUpdateSerializer
from listings.api.serializers import CropSerializer
from listings.api.serializers import MarketplaceQuerySerializer
from listings.api.serializers import ProductCreateSerializer
from listings.api.serializers import ProductSerializer
from listings.api.serializers import ProductUpdateSerializer
from listings.services.marketplace_service import MarketplaceService


class CropListCreateView(APIView):
    """List crop categories and create new categories as admin."""

    permission_classes = [permissions.IsAuthenticated, IsVerifiedRole]

    def get(self, request):
        """Return active crop categories."""
        service = MarketplaceService()
        crops = service.list_crops()
        return Response(CropSerializer(crops, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new crop category."""
        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication credentials were not provided.'}, status=401)
        serializer = CropCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = MarketplaceService()
        crop = service.create_crop(actor=request.user, **serializer.validated_data)
        return Response(CropSerializer(crop).data, status=status.HTTP_201_CREATED)


class CropDetailView(APIView):
    """Retrieve, update, and delete a single crop category."""

    permission_classes = [permissions.IsAuthenticated, IsVerifiedRole]

    def patch(self, request, crop_id):
        """Update crop fields for admin."""
        serializer = CropUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = MarketplaceService()
        crop = service.update_crop(
            actor=request.user,
            crop_id=crop_id,
            **serializer.validated_data,
        )
        return Response(CropSerializer(crop).data, status=status.HTTP_200_OK)

    def delete(self, request, crop_id):
        """Deactivate a crop category as admin."""
        service = MarketplaceService()
        service.delete_crop(actor=request.user, crop_id=crop_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductListCreateView(APIView):
    """List available products and create new seller listings."""

    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsVerifiedRole]

    def get(self, request):
        """Return filtered available marketplace listings."""
        query_serializer = MarketplaceQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        service = MarketplaceService()
        products = service.list_available_products(**query_serializer.validated_data)
        return Response(ProductSerializer(products, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new product listing for the authenticated seller."""
        if not IsSellerOrAdmin().has_permission(request, self):
            return Response({'detail': 'You do not have permission to perform this action.'}, status=403)
        serializer = ProductCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = MarketplaceService()
        product = service.create_product(actor=request.user, **serializer.validated_data)
        return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)


class MyProductListView(APIView):
    """List products owned by the authenticated seller."""

    permission_classes = [permissions.IsAuthenticated, IsSellerOrAdmin, IsVerifiedRole]

    def get(self, request):
        """Return products for the current authenticated seller."""
        service = MarketplaceService()
        products = service.list_my_products(actor=request.user, status=request.query_params.get('status'))
        return Response(ProductSerializer(products, many=True).data, status=status.HTTP_200_OK)


class ProductDetailView(APIView):
    """Retrieve, update, and delete a single marketplace listing."""

    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsVerifiedRole]

    def get(self, request, product_id):
        """Return product details by identifier."""
        service = MarketplaceService()
        product = service.get_product(product_id=product_id)
        return Response(ProductSerializer(product).data, status=status.HTTP_200_OK)

    def patch(self, request, product_id):
        """Update product fields for the owner seller or admin."""
        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication credentials were not provided.'}, status=401)
        serializer = ProductUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = MarketplaceService()
        product = service.update_product(
            actor=request.user,
            product_id=product_id,
            **serializer.validated_data,
        )
        return Response(ProductSerializer(product).data, status=status.HTTP_200_OK)

    def delete(self, request, product_id):
        """Delete a listing as owner seller or admin."""
        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication credentials were not provided.'}, status=401)
        service = MarketplaceService()
        service.delete_product(actor=request.user, product_id=product_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
