"""Initial marketplace app migration."""

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    """Create crop and product listing tables."""

    initial = True

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Crop',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=120, unique=True)),
                ('slug', models.SlugField(max_length=140, unique=True)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'crops',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=160)),
                ('description', models.TextField(blank=True)),
                ('unit', models.CharField(choices=[('kg', 'Kilogram'), ('ton', 'Ton'), ('bag', 'Bag'), ('crate', 'Crate')], max_length=16)),
                ('price_per_unit', models.DecimalField(decimal_places=2, max_digits=12)),
                ('quantity_available', models.DecimalField(decimal_places=3, max_digits=12)),
                ('minimum_order_quantity', models.DecimalField(decimal_places=3, default=1, max_digits=12)),
                ('location_name', models.CharField(max_length=120)),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('available_from', models.DateField(default=django.utils.timezone.localdate)),
                ('expires_at', models.DateTimeField()),
                ('status', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive'), ('sold_out', 'Sold Out'), ('expired', 'Expired')], default='active', max_length=16)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('crop', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='products', to='listings.crop')),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='marketplace_products', to='users.user')),
            ],
            options={
                'db_table': 'products',
                'ordering': ['-created_at'],
                'constraints': [
                    models.CheckConstraint(condition=models.Q(('price_per_unit__gt', 0)), name='products_price_per_unit_gt_zero'),
                    models.CheckConstraint(condition=models.Q(('quantity_available__gte', 0)), name='products_quantity_available_gte_zero'),
                    models.CheckConstraint(condition=models.Q(('minimum_order_quantity__gt', 0)), name='products_minimum_order_quantity_gt_zero'),
                ],
            },
        ),
    ]
