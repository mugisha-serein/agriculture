"""Add verification fraud checks."""

from django.db import migrations, models
import django.db.models.deletion


def backfill_fraud_checks(apps, schema_editor):
    UserVerification = apps.get_model('verification', 'UserVerification')
    VerificationFraudCheck = apps.get_model('verification', 'VerificationFraudCheck')

    for verification in UserVerification.objects.all():
        VerificationFraudCheck.objects.create(
            verification_id=verification.id,
            risk_score=0,
            risk_level='low',
            verdict='clear',
            signals={'backfilled': True},
            is_flagged=False,
            checked_at=verification.submitted_at,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('verification', '0008_verification_status_logs'),
    ]

    operations = [
        migrations.CreateModel(
            name='VerificationFraudCheck',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('risk_score', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('risk_level', models.CharField(blank=True, max_length=16)),
                ('verdict', models.CharField(blank=True, max_length=32)),
                ('signals', models.JSONField(default=dict)),
                ('is_flagged', models.BooleanField(default=False)),
                ('checked_at', models.DateTimeField()),
                (
                    'verification',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='fraud_checks',
                        to='verification.userverification',
                    ),
                ),
            ],
            options={
                'db_table': 'verification_fraud_checks',
                'ordering': ['-checked_at'],
            },
        ),
        migrations.RunPython(backfill_fraud_checks, migrations.RunPython.noop),
    ]
