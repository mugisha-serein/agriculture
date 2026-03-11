"""Add verification documents and migrate document fields."""

import hashlib

import django.db.models.deletion
from django.db import migrations, models


def _normalize_document_number(document_number):
    return ''.join((document_number or '').strip().upper().split())


def _hash_document_number(document_number):
    normalized = _normalize_document_number(document_number)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def _document_number_last4(document_number):
    normalized = _normalize_document_number(document_number)
    return normalized[-4:] if len(normalized) >= 4 else normalized


def migrate_documents(apps, schema_editor):
    UserVerification = apps.get_model('verification', 'UserVerification')
    VerificationDocument = apps.get_model('verification', 'VerificationDocument')

    for verification in UserVerification.objects.all().only(
        'id',
        'document_type',
        'document_number',
        'document_front',
        'document_back',
        'selfie',
    ):
        front_name = getattr(verification.document_front, 'name', '') if verification.document_front else ''
        back_name = getattr(verification.document_back, 'name', '') if verification.document_back else ''
        selfie_name = getattr(verification.selfie, 'name', '') if verification.selfie else ''
        VerificationDocument.objects.create(
            verification_id=verification.id,
            document_type_id=verification.document_type_id,
            document_number_hash=_hash_document_number(verification.document_number),
            document_number_last4=_document_number_last4(verification.document_number),
            document_front=verification.document_front,
            document_back=verification.document_back,
            selfie=verification.selfie,
            document_metadata={
                'migrated': True,
                'front_name': front_name,
                'back_name': back_name,
                'selfie_name': selfie_name,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('verification', '0003_userverification_refactor'),
    ]

    operations = [
        migrations.CreateModel(
            name='VerificationDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('document_number_hash', models.CharField(max_length=64)),
                ('document_number_last4', models.CharField(blank=True, max_length=4)),
                ('document_front', models.FileField(upload_to='verification/front/')),
                ('document_back', models.FileField(blank=True, null=True, upload_to='verification/back/')),
                ('selfie', models.FileField(blank=True, null=True, upload_to='verification/selfie/')),
                ('document_metadata', models.JSONField(default=dict)),
                (
                    'document_type',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='documents',
                        to='verification.verificationdocumenttype',
                    ),
                ),
                (
                    'verification',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='documents',
                        to='verification.userverification',
                    ),
                ),
            ],
            options={
                'db_table': 'verification_documents',
                'ordering': ['-created_at'],
            },
        ),
        migrations.RunPython(migrate_documents, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='userverification',
            name='document_type',
        ),
        migrations.RemoveField(
            model_name='userverification',
            name='document_number',
        ),
        migrations.RemoveField(
            model_name='userverification',
            name='document_front',
        ),
        migrations.RemoveField(
            model_name='userverification',
            name='document_back',
        ),
        migrations.RemoveField(
            model_name='userverification',
            name='selfie',
        ),
    ]
