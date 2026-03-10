"""Initial reputation app migration."""

import django.core.validators
import django.db.models.deletion
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    """Create reviews table for trust and reputation."""

    initial = True

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('rating', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('comment', models.TextField(blank=True)),
                ('is_visible', models.BooleanField(default=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='reviews', to='orders.order')),
                ('reviewee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews_received', to='users.user')),
                ('reviewer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews_given', to='users.user')),
            ],
            options={
                'db_table': 'reviews',
                'ordering': ['-created_at'],
                'constraints': [
                    models.UniqueConstraint(fields=('order', 'reviewer', 'reviewee'), name='unique_review_per_order_reviewer_reviewee'),
                    models.CheckConstraint(condition=~models.Q(reviewer=models.F('reviewee')), name='reviews_reviewer_not_reviewee'),
                ],
            },
        ),
    ]
