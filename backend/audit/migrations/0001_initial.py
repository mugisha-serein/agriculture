"""Initial audit app migration."""

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    """Create immutable audit event table."""

    initial = True

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request_id', models.CharField(blank=True, max_length=64)),
                ('actor_email', models.EmailField(blank=True, max_length=254)),
                ('source', models.CharField(default='model_signal', max_length=32)),
                ('action', models.CharField(choices=[('create', 'Create'), ('update', 'Update'), ('delete', 'Delete'), ('custom', 'Custom')], max_length=16)),
                ('app_label', models.CharField(max_length=64)),
                ('model_label', models.CharField(max_length=128)),
                ('object_pk', models.CharField(max_length=64)),
                ('object_repr', models.CharField(blank=True, max_length=255)),
                ('request_path', models.CharField(blank=True, max_length=255)),
                ('request_method', models.CharField(blank=True, max_length=16)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.CharField(blank=True, max_length=512)),
                ('before_state', models.JSONField(default=dict)),
                ('after_state', models.JSONField(default=dict)),
                ('change_set', models.JSONField(default=dict)),
                ('metadata', models.JSONField(default=dict)),
                ('previous_hash', models.CharField(blank=True, max_length=64)),
                ('event_hash', models.CharField(max_length=64, unique=True)),
                ('occurred_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_events', to='users.user')),
            ],
            options={
                'db_table': 'audit_events',
                'ordering': ['-id'],
            },
        ),
    ]
