"""Add verification status logs."""

from django.db import migrations, models
import django.db.models.deletion


def backfill_status_logs(apps, schema_editor):
    UserVerification = apps.get_model('verification', 'UserVerification')
    VerificationStatusLog = apps.get_model('verification', 'VerificationStatusLog')

    for verification in UserVerification.objects.all():
        submitted_at = verification.submitted_at
        VerificationStatusLog.objects.create(
            verification_id=verification.id,
            previous_status=verification.status,
            new_status=verification.status,
            changed_at=submitted_at,
            change_reason='submitted',
            change_metadata={'backfilled': True},
        )
        if verification.reviewed_at:
            VerificationStatusLog.objects.create(
                verification_id=verification.id,
                previous_status='pending',
                new_status=verification.status,
                changed_at=verification.reviewed_at,
                change_reason='reviewed',
                change_metadata={'backfilled': True},
            )


class Migration(migrations.Migration):

    dependencies = [
        ('verification', '0007_verification_reviews'),
    ]

    operations = [
        migrations.CreateModel(
            name='VerificationStatusLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('previous_status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], max_length=16)),
                ('new_status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], max_length=16)),
                ('changed_at', models.DateTimeField()),
                ('change_reason', models.CharField(blank=True, max_length=255)),
                ('change_metadata', models.JSONField(default=dict)),
                (
                    'verification',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='status_logs',
                        to='verification.userverification',
                    ),
                ),
            ],
            options={
                'db_table': 'verification_status_logs',
                'ordering': ['-changed_at'],
            },
        ),
        migrations.RunPython(backfill_status_logs, migrations.RunPython.noop),
    ]
