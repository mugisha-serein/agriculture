"""Identity API views."""

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from users.api.serializers import (
    ActivationSerializer,
    LoginSerializer,
    LogoutSerializer,
    RefreshSerializer,
    RegistrationSerializer,
    TokenVerifySerializer,
)
from users.services.identity_service import IdentityService


class RegistrationView(APIView):
    """Register a new inactive user account."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Handle registration requests."""
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = IdentityService()
        result = service.register_user(**serializer.validated_data)
        return Response(
            {
                'user': {
                    'id': result.user.id,
                    'email': result.user.email,
                    'first_name': result.user.first_name,
                    'last_name': result.user.last_name,
                    'phone': result.user.phone,
                    'role': result.user.role,
                    'is_active': result.user.is_active,
                    'is_verified': result.user.is_verified,
                },
                'activation_token': result.activation_token,
            },
            status=status.HTTP_201_CREATED,
        )


class ActivationView(APIView):
    """Activate an existing user account."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Handle activation requests."""
        serializer = ActivationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = IdentityService()
        user = service.activate_account(token=serializer.validated_data['token'])
        return Response(
            {
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone': user.phone,
                    'role': user.role,
                    'is_active': user.is_active,
                    'is_verified': user.is_verified,
                }
            },
            status=status.HTTP_200_OK,
        )


class LoginView(APIView):
    """Authenticate user credentials and issue JWT tokens."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Handle login requests."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = IdentityService()
        result = service.login(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
            user_agent=serializer.validated_data.get('user_agent', ''),
            ip_address=self._resolve_ip_address(request),
        )
        return Response(
            {
                'user': {
                    'id': result.user.id,
                    'email': result.user.email,
                    'first_name': result.user.first_name,
                    'last_name': result.user.last_name,
                    'phone': result.user.phone,
                    'role': result.user.role,
                    'is_verified': result.user.is_verified,
                },
                'session_id': result.session.id,
                'access_token': result.access_token,
                'refresh_token': result.refresh_token,
                'access_expires_at': result.access_expires_at,
                'refresh_expires_at': result.refresh_expires_at,
            },
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _resolve_ip_address(request):
        """Resolve the client IP address from request metadata."""
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded:
            return forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class RefreshView(APIView):
    """Rotate a refresh token and issue a new token pair."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Handle refresh requests."""
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = IdentityService()
        result = service.refresh(refresh_token=serializer.validated_data['refresh_token'])
        return Response(
            {
                'session_id': result.session.id,
                'access_token': result.access_token,
                'refresh_token': result.refresh_token,
                'access_expires_at': result.access_expires_at,
                'refresh_expires_at': result.refresh_expires_at,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """Revoke refresh token and corresponding session."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Handle logout requests."""
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = IdentityService()
        service.logout(refresh_token=serializer.validated_data['refresh_token'])
        return Response({'detail': 'Logged out.'}, status=status.HTTP_200_OK)


class TokenVerifyView(APIView):
    """Validate access token integrity and expiry."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Handle token verification requests."""
        serializer = TokenVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = IdentityService()
        payload = service.validate_access_token(
            access_token=serializer.validated_data['access_token']
        )
        return Response({'is_valid': True, 'payload': payload}, status=status.HTTP_200_OK)
