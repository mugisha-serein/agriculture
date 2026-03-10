"""Add request-level audit action table."""

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    """Create audit request action model for managed app action tracking."""

    dependencies = [
        ('audit', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditRequestAction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request_id', models.CharField(blank=True, max_length=64)),
                ('actor_email', models.EmailField(blank=True, max_length=254)),
                ('app_scope', models.CharField(max_length=32)),
                ('action_name', models.CharField(max_length=128)),
                ('request_path', models.CharField(max_length=255)),
                ('request_method', models.CharField(max_length=16)),
                ('status_code', models.PositiveSmallIntegerField(default=0)),
                ('succeeded', models.BooleanField(default=False)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.CharField(blank=True, max_length=512)),
                ('query_params', models.JSONField(default=dict)),
                ('request_data', models.JSONField(default=dict)),
                ('response_data', models.JSONField(default=dict)),
                ('metadata', models.JSONField(default=dict)),
                ('duration_ms', models.PositiveIntegerField(default=0)),
                ('previous_hash', models.CharField(blank=True, max_length=64)),
                ('event_hash', models.CharField(max_length=64, unique=True)),
                ('management_status', models.CharField(choices=[('new', 'New'), ('in_review', 'In Review'), ('resolved', 'Resolved'), ('escalated', 'Escalated')], default='new', max_length=16)),
                ('management_note', models.TextField(blank=True)),
                ('managed_at', models.DateTimeField(blank=True, null=True)),
                ('occurred_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_request_actions', to='users.user')),
                ('managed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='managed_audit_request_actions', to='users.user')),
            ],
            options={
                'db_table': 'audit_request_actions',
                'ordering': ['-id'],
            },
        ),
    ]
