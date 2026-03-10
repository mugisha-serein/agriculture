"""Initial discovery app migration."""

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    """Create search query telemetry table."""

    initial = True

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SearchQueryLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('query_text', models.CharField(blank=True, max_length=255)),
                ('filters', models.JSONField(default=dict)),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('radius_km', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('sort_by', models.CharField(choices=[('relevance', 'Relevance'), ('price_asc', 'Price Low To High'), ('price_desc', 'Price High To Low'), ('newest', 'Newest'), ('distance', 'Distance')], default='relevance', max_length=16)),
                ('page', models.PositiveIntegerField(default=1)),
                ('page_size', models.PositiveIntegerField(default=20)),
                ('result_count', models.PositiveIntegerField(default=0)),
                ('searched_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('searched_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='discovery_search_logs', to='users.user')),
            ],
            options={
                'db_table': 'search_queries',
                'ordering': ['-searched_at'],
            },
        ),
    ]
