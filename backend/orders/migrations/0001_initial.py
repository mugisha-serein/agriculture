"""Initial orders app migration."""

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    """Create orders and order items tables."""

    initial = True

    dependencies = [
        ('listings', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('order_number', models.CharField(max_length=32, unique=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled'), ('completed', 'Completed')], default='pending', max_length=16)),
                ('currency', models.CharField(default='ZAR', max_length=8)),
                ('subtotal_amount', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('seller_count', models.PositiveIntegerField(default=0)),
                ('item_count', models.PositiveIntegerField(default=0)),
                ('notes', models.TextField(blank=True)),
                ('placed_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('confirmed_at', models.DateTimeField(blank=True, null=True)),
                ('cancelled_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('cancellation_reason', models.TextField(blank=True)),
                ('buyer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='purchase_orders', to='users.user')),
            ],
            options={
                'db_table': 'orders',
                'ordering': ['-placed_at'],
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product_title', models.CharField(max_length=160)),
                ('unit', models.CharField(max_length=16)),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('quantity', models.DecimalField(decimal_places=3, max_digits=12)),
                ('line_total', models.DecimalField(decimal_places=2, max_digits=14)),
                ('status', models.CharField(choices=[('allocated', 'Allocated'), ('fulfilled', 'Fulfilled'), ('cancelled', 'Cancelled')], default='allocated', max_length=16)),
                ('allocated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('fulfilled_at', models.DateTimeField(blank=True, null=True)),
                ('cancelled_at', models.DateTimeField(blank=True, null=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='orders.order')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='order_items', to='listings.product')),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sales_order_items', to='users.user')),
            ],
            options={
                'db_table': 'order_items',
                'ordering': ['id'],
            },
        ),
    ]
