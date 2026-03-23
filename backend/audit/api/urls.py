"""URL routing for audit APIs."""

from django.urls import path

from audit.api.views import AuditEventListView
from audit.api.views import AuditExportView
from audit.api.views import AuditRequestActionListView
from audit.api.views import AuditRequestActionManageView

app_name = 'audit'

urlpatterns = [
    path('events/', AuditEventListView.as_view(), name='events'),
    path('exports/', AuditExportView.as_view(), name='exports'),
    path('actions/', AuditRequestActionListView.as_view(), name='actions'),
    path('actions/<int:action_id>/manage/', AuditRequestActionManageView.as_view(), name='manage-action'),
]
