from django.conf import settings
from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0002_auditrequestaction'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alert_type', models.CharField(choices=[('admin_privilege_change', 'Admin Privilege Change'), ('large_refund', 'Large Refund'), ('account_suspension', 'Account Suspension')], max_length=32)),
                ('severity', models.CharField(choices=[('warning', 'Warning'), ('critical', 'Critical')], default='warning', max_length=16)),
                ('description', models.CharField(max_length=255)),
                ('context', models.JSONField(default=dict)),
                ('triggered_at', models.DateTimeField(default=timezone.now)),
                ('event', models.ForeignKey(on_delete=models.CASCADE, related_name='alerts', to='audit.auditevent')),
                ('triggered_by', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='audit_alerts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'audit_alerts',
                'ordering': ['-triggered_at'],
            },
        ),
    ]
