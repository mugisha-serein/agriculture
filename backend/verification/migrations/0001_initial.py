"""Initial verification app migration."""

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    """Create user verification table and constraints."""

    initial = True

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserVerification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=16)),
                ('document_type', models.CharField(choices=[('national_id', 'National ID'), ('passport', 'Passport'), ('driver_license', 'Driver License'), ('business_registration', 'Business Registration')], max_length=32)),
                ('document_number', models.CharField(max_length=64)),
                ('document_front', models.FileField(upload_to='verification/front/')),
                ('document_back', models.FileField(blank=True, null=True, upload_to='verification/back/')),
                ('selfie', models.FileField(blank=True, null=True, upload_to='verification/selfie/')),
                ('submitted_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('admin_notes', models.TextField(blank=True)),
                ('rejection_reason', models.TextField(blank=True)),
                ('is_current', models.BooleanField(default=True)),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_verifications', to='users.user')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='verifications', to='users.user')),
            ],
            options={
                'db_table': 'user_verifications',
                'ordering': ['-submitted_at'],
                'constraints': [models.UniqueConstraint(condition=models.Q(('is_current', True)), fields=('user',), name='unique_current_verification_per_user')],
            },
        ),
    ]
