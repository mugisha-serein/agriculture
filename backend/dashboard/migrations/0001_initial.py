from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('listings', '0001_initial'),
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DailySalesMetric',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('date', models.DateField(unique=True)),
                ('gmv', models.DecimalField(decimal_places=2, default=0.0, max_digits=16)),
                ('orders_count', models.PositiveIntegerField(default=0)),
                ('active_sellers', models.PositiveIntegerField(default=0)),
                ('conversion_rate', models.DecimalField(decimal_places=4, default=0.0, max_digits=5)),
                ('cart_abandonment_rate', models.DecimalField(decimal_places=4, default=0.0, max_digits=5)),
                ('delivery_success_rate', models.DecimalField(decimal_places=4, default=0.0, max_digits=5)),
            ],
            options={'db_table': 'daily_sales_metrics', 'ordering': ['-date']},
        ),
        migrations.CreateModel(
            name='ProductPerformance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('date', models.DateField()),
                ('units_sold', models.DecimalField(decimal_places=3, default=0.0, max_digits=14)),
                ('revenue', models.DecimalField(decimal_places=2, default=0.0, max_digits=16)),
                ('conversion_rate', models.DecimalField(decimal_places=4, default=0.0, max_digits=5)),
                ('cart_abandonment_count', models.PositiveIntegerField(default=0)),
                ('product', models.ForeignKey(on_delete=models.CASCADE, related_name='performances', to='listings.product')),
            ],
            options={'db_table': 'product_performance', 'ordering': ['-date'], 'unique_together': {('product', 'date')}},
        ),
        migrations.CreateModel(
            name='SellerPerformance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('date', models.DateField()),
                ('gmv', models.DecimalField(decimal_places=2, default=0.0, max_digits=16)),
                ('orders_count', models.PositiveIntegerField(default=0)),
                ('delivery_success_rate', models.DecimalField(decimal_places=4, default=0.0, max_digits=5)),
                ('fulfillment_rate', models.DecimalField(decimal_places=4, default=0.0, max_digits=5)),
                ('rating_score', models.DecimalField(decimal_places=4, default=0.0, max_digits=5)),
                ('seller', models.ForeignKey(on_delete=models.CASCADE, related_name='performance_records', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'seller_performance', 'ordering': ['-date'], 'unique_together': {('seller', 'date')}},
        ),
        migrations.CreateModel(
            name='BuyerActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('date', models.DateField()),
                ('orders_count', models.PositiveIntegerField(default=0)),
                ('total_spend', models.DecimalField(decimal_places=2, default=0.0, max_digits=16)),
                ('average_cart_value', models.DecimalField(decimal_places=2, default=0.0, max_digits=16)),
                ('cart_abandonment_rate', models.DecimalField(decimal_places=4, default=0.0, max_digits=5)),
                ('last_active_at', models.DateTimeField()),
                ('buyer', models.ForeignKey(on_delete=models.CASCADE, related_name='activity_records', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'buyer_activity', 'ordering': ['-date'], 'unique_together': {('buyer', 'date')}},
        ),
    ]
