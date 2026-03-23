"""API views for querying immutable audit events."""

from rest_framework import permissions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from audit.api.permissions import IsAuditAdmin
from audit.api.serializers import AuditEventQuerySerializer
from audit.api.serializers import AuditEventSerializer
from audit.api.serializers import AuditExportQuerySerializer
from audit.api.serializers import AuditRequestActionManageSerializer
from audit.api.serializers import AuditRequestActionQuerySerializer
from audit.api.serializers import AuditRequestActionSerializer
from audit.models import AuditEvent
from audit.models import AuditRequestAction
from audit.services.export_service import AuditExportService


class AuditEventListView(APIView):
    """List immutable audit events for admin actors."""

    permission_classes = [permissions.IsAuthenticated, IsAuditAdmin]

    def get(self, request):
        """Return paginated audit events with optional filters."""
        query_serializer = AuditEventQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        filters = query_serializer.validated_data
        queryset = AuditEvent.objects.select_related('actor').all()

        if 'request_id' in filters:
            queryset = queryset.filter(request_id=filters['request_id'])
        if 'actor_id' in filters:
            queryset = queryset.filter(actor_id=filters['actor_id'])
        if 'action' in filters:
            queryset = queryset.filter(action=filters['action'])
        if 'app_label' in filters:
            queryset = queryset.filter(app_label=filters['app_label'])
        if 'model_label' in filters:
            queryset = queryset.filter(model_label=filters['model_label'])
        if 'object_pk' in filters:
            queryset = queryset.filter(object_pk=str(filters['object_pk']))

        page = filters['page']
        page_size = filters['page_size']
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        rows = queryset[start:end]

        return Response(
            {
                'results': AuditEventSerializer(rows, many=True).data,
                'pagination': {
                    'total_count': total_count,
                    'page': page,
                    'page_size': page_size,
                },
            },
            status=status.HTTP_200_OK,
        )


class AuditRequestActionListView(APIView):
    """List request-level action logs for managed app scopes."""

    permission_classes = [permissions.IsAuthenticated, IsAuditAdmin]

    def get(self, request):
        """Return paginated request action logs with optional filters."""
        query_serializer = AuditRequestActionQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        filters = query_serializer.validated_data
        queryset = AuditRequestAction.objects.select_related('actor', 'managed_by').all()

        if 'request_id' in filters:
            queryset = queryset.filter(request_id=filters['request_id'])
        if 'actor_id' in filters:
            queryset = queryset.filter(actor_id=filters['actor_id'])
        if 'app_scope' in filters:
            queryset = queryset.filter(app_scope=filters['app_scope'])
        if 'request_method' in filters:
            queryset = queryset.filter(request_method__iexact=filters['request_method'])
        if 'status_code' in filters:
            queryset = queryset.filter(status_code=filters['status_code'])
        if 'management_status' in filters:
            queryset = queryset.filter(management_status=filters['management_status'])

        page = filters['page']
        page_size = filters['page_size']
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        rows = queryset[start:end]

        return Response(
            {
                'results': AuditRequestActionSerializer(rows, many=True).data,
                'pagination': {
                    'total_count': total_count,
                    'page': page,
                    'page_size': page_size,
                },
            },
            status=status.HTTP_200_OK,
        )


class AuditRequestActionManageView(APIView):
    """Manage workflow state for one request-level audit action."""

    permission_classes = [permissions.IsAuthenticated, IsAuditAdmin]

    def post(self, request, action_id):
        """Update management status and note for selected action."""
        serializer = AuditRequestActionManageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            action_row = AuditRequestAction.objects.get(id=action_id)
        except AuditRequestAction.DoesNotExist:
            return Response({'detail': 'Audit action was not found.'}, status=status.HTTP_404_NOT_FOUND)

        action_row.management_status = serializer.validated_data['management_status']
        action_row.management_note = serializer.validated_data.get('management_note', '')
        action_row.managed_by = request.user
        action_row.managed_at = timezone.now()
        action_row.save(
            update_fields=['management_status', 'management_note', 'managed_by', 'managed_at']
        )
        return Response(AuditRequestActionSerializer(action_row).data, status=status.HTTP_200_OK)


class AuditExportView(APIView):
    """Provide export-ready audit payloads for regulated audiences."""

    permission_classes = [permissions.IsAuthenticated, IsAuditAdmin]

    def get(self, request):
        """Return serialized audit payloads scoped for the requested audience."""
        serializer = AuditExportQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        export_payload = AuditExportService().export(
            audience=serializer.validated_data['audience'],
            since=serializer.validated_data.get('since'),
            limit=serializer.validated_data.get('limit'),
        )
        return Response(export_payload, status=status.HTTP_200_OK)
