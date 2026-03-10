"""Initial logistics app migration."""

import django.db.models.deletion
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    """Create shipments table for logistics coordination."""

    initial = True

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Shipment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('shipment_reference', models.CharField(max_length=40, unique=True)),
                ('tracking_code', models.CharField(max_length=40, unique=True)),
                ('status', models.CharField(choices=[('pending_assignment', 'Pending Assignment'), ('assigned', 'Assigned'), ('picked_up', 'Picked Up'), ('in_transit', 'In Transit'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled')], default='pending_assignment', max_length=24)),
                ('pickup_address', models.CharField(max_length=255)),
                ('delivery_address', models.CharField(max_length=255)),
                ('scheduled_pickup_at', models.DateTimeField(blank=True, null=True)),
                ('assigned_at', models.DateTimeField(blank=True, null=True)),
                ('picked_up_at', models.DateTimeField(blank=True, null=True)),
                ('in_transit_at', models.DateTimeField(blank=True, null=True)),
                ('delivered_at', models.DateTimeField(blank=True, null=True)),
                ('cancelled_at', models.DateTimeField(blank=True, null=True)),
                ('delivery_confirmed_at', models.DateTimeField(blank=True, null=True)),
                ('last_location_note', models.CharField(blank=True, max_length=255)),
                ('delivery_proof', models.TextField(blank=True)),
                ('delivery_confirmation_note', models.TextField(blank=True)),
                ('cancellation_reason', models.TextField(blank=True)),
                ('buyer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='buyer_shipments', to='users.user')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='created_shipments', to='users.user')),
                ('delivered_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='delivered_shipments', to='users.user')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='shipments', to='orders.order')),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='seller_shipments', to='users.user')),
                ('transporter', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='transporter_shipments', to='users.user')),
            ],
            options={
                'db_table': 'shipments',
                'ordering': ['-created_at'],
            },
        ),
    ]
