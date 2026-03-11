"""Add verification selfies and migrate selfie files."""

import django.db.models.deletion
from django.db import migrations, models


def migrate_selfies(apps, schema_editor):
    VerificationDocument = apps.get_model('verification', 'VerificationDocument')
    VerificationSelfie = apps.get_model('verification', 'VerificationSelfie')

    for document in VerificationDocument.objects.exclude(selfie=''):
        if not document.selfie:
            continue
        VerificationSelfie.objects.create(
            verification_id=document.verification_id,
            document_id=document.id,
            image=document.selfie,
            comparison_metadata={'migrated': True},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('verification', '0005_document_type_requirements'),
    ]

    operations = [
        migrations.CreateModel(
            name='VerificationSelfie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('image', models.FileField(upload_to='verification/selfie/')),
                ('face_match_score', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('face_match_status', models.CharField(blank=True, max_length=32)),
                ('comparison_provider', models.CharField(blank=True, max_length=64)),
                ('comparison_metadata', models.JSONField(default=dict)),
                ('compared_at', models.DateTimeField(blank=True, null=True)),
                (
                    'document',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='selfies',
                        to='verification.verificationdocument',
                    ),
                ),
                (
                    'verification',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='selfies',
                        to='verification.userverification',
                    ),
                ),
            ],
            options={
                'db_table': 'verification_selfies',
                'ordering': ['-created_at'],
            },
        ),
        migrations.RunPython(migrate_selfies, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='verificationdocument',
            name='selfie',
        ),
    ]
