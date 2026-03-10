"""Initial payments app migration."""

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    """Create payments and escrow transaction tables."""

    initial = True

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('payment_reference', models.CharField(max_length=40, unique=True)),
                ('status', models.CharField(choices=[('initiated', 'Initiated'), ('escrow_held', 'Escrow Held'), ('released', 'Released'), ('refunded', 'Refunded'), ('failed', 'Failed')], default='initiated', max_length=16)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=14)),
                ('currency', models.CharField(default='ZAR', max_length=8)),
                ('idempotency_key', models.CharField(max_length=120)),
                ('request_fingerprint', models.CharField(max_length=64)),
                ('provider', models.CharField(default='mock_gateway', max_length=64)),
                ('provider_payment_id', models.CharField(blank=True, max_length=128)),
                ('failure_code', models.CharField(blank=True, max_length=64)),
                ('failure_message', models.CharField(blank=True, max_length=255)),
                ('initiated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('escrow_held_at', models.DateTimeField(blank=True, null=True)),
                ('released_at', models.DateTimeField(blank=True, null=True)),
                ('refunded_at', models.DateTimeField(blank=True, null=True)),
                ('processed_webhook_ids', models.JSONField(default=list)),
                ('buyer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='payments', to='users.user')),
                ('order', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='payment', to='orders.order')),
            ],
            options={
                'db_table': 'payments',
                'ordering': ['-initiated_at'],
                'constraints': [models.UniqueConstraint(fields=('buyer', 'idempotency_key'), name='unique_payment_idempotency_per_buyer')],
            },
        ),
        migrations.CreateModel(
            name='EscrowTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_reference', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('transaction_type', models.CharField(choices=[('hold', 'Hold'), ('release', 'Release'), ('refund', 'Refund')], max_length=16)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=14)),
                ('currency', models.CharField(default='ZAR', max_length=8)),
                ('external_reference', models.CharField(blank=True, max_length=120, unique=True)),
                ('metadata', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='created_escrow_transactions', to='users.user')),
                ('payment', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='escrow_transactions', to='payments.payment')),
            ],
            options={
                'db_table': 'escrow_transactions',
                'ordering': ['created_at'],
            },
        ),
    ]
