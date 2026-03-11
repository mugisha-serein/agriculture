"""API views for verification workflows."""

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from verification.api.permissions import IsVerificationAdmin
from verification.api.serializers import VerificationReviewInputSerializer
from verification.api.serializers import VerificationSubmissionSerializer
from verification.api.serializers import VerificationSummarySerializer
from verification.services.verification_service import VerificationService


class SubmitVerificationView(APIView):
    """Submit a KYC verification request."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Handle verification submission requests."""
        serializer = VerificationSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data.copy()
        activation_token = data.pop('activation_token', None)
        
        user = None
        if activation_token:
            from users.services.identity_service import IdentityService
            identity_service = IdentityService()
            user = identity_service.get_user_from_activation_token(activation_token)
        elif request.user and request.user.is_authenticated:
            user = request.user
        else:
            return Response({'detail': 'Authentication or activation token required.'}, status=status.HTTP_401_UNAUTHORIZED)

        service = VerificationService()
        verification = service.submit_verification(user=user, **data)
        return Response(
            VerificationSummarySerializer(verification).data,
            status=status.HTTP_201_CREATED,
        )


class MyVerificationView(APIView):
    """Return the current verification record for the authenticated user."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Handle retrieval of the current user verification."""
        service = VerificationService()
        verification = service.get_current_verification(user=request.user)
        if verification is None:
            return Response({'detail': 'No verification found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(VerificationSummarySerializer(verification).data, status=status.HTTP_200_OK)


class AdminPendingVerificationListView(APIView):
    """List pending verifications for administrative review."""

    permission_classes = [permissions.IsAuthenticated, IsVerificationAdmin]

    def get(self, request):
        """Handle pending verification listing."""
        service = VerificationService()
        pending = service.list_pending()
        data = VerificationSummarySerializer(pending, many=True).data
        return Response(data, status=status.HTTP_200_OK)


class AdminReviewVerificationView(APIView):
    """Review a pending verification as an administrator."""

    permission_classes = [permissions.IsAuthenticated, IsVerificationAdmin]

    def post(self, request, verification_id):
        """Handle verification decision submission."""
        serializer = VerificationReviewInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = VerificationService()
        verification = service.review_verification(
            reviewer=request.user,
            verification_id=verification_id,
            decision=serializer.validated_data['status'],
            review_notes=serializer.validated_data.get('review_notes', ''),
            rejection_reason=serializer.validated_data.get('rejection_reason', ''),
        )
        return Response(VerificationSummarySerializer(verification).data, status=status.HTTP_200_OK)
