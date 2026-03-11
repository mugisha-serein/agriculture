"""Add verification review history records."""

from django.db import migrations, models
import django.db.models.deletion


def backfill_reviews(apps, schema_editor):
    UserVerification = apps.get_model('verification', 'UserVerification')
    VerificationReview = apps.get_model('verification', 'VerificationReview')

    for verification in UserVerification.objects.exclude(reviewed_at__isnull=True):
        VerificationReview.objects.create(
            verification_id=verification.id,
            reviewer_id=verification.reviewed_by_id,
            previous_status='pending',
            new_status=verification.status,
            review_notes=verification.review_notes,
            rejection_reason=verification.rejection_reason,
            reviewed_at=verification.reviewed_at,
            review_metadata={'backfilled': True},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('verification', '0006_verification_selfies'),
    ]

    operations = [
        migrations.CreateModel(
            name='VerificationReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('previous_status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], max_length=16)),
                ('new_status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], max_length=16)),
                ('review_notes', models.TextField(blank=True)),
                ('rejection_reason', models.TextField(blank=True)),
                ('reviewed_at', models.DateTimeField()),
                ('review_metadata', models.JSONField(default=dict)),
                (
                    'reviewer',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='verification_reviews',
                        to='users.user',
                    ),
                ),
                (
                    'verification',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='reviews',
                        to='verification.userverification',
                    ),
                ),
            ],
            options={
                'db_table': 'verification_reviews',
                'ordering': ['-reviewed_at'],
            },
        ),
        migrations.RunPython(backfill_reviews, migrations.RunPython.noop),
    ]
