"""Add document type model and migrate verification records."""

import django.db.models.deletion
from django.db import migrations, models


DOCUMENT_TYPES = [
    ('national_id', 'National ID'),
    ('passport', 'Passport'),
    ('driver_license', 'Driver License'),
    ('business_registration', 'Business Registration'),
]


def seed_document_types(apps, schema_editor):
    VerificationDocumentType = apps.get_model('verification', 'VerificationDocumentType')
    UserVerification = apps.get_model('verification', 'UserVerification')

    for code, name in DOCUMENT_TYPES:
        VerificationDocumentType.objects.get_or_create(
            code=code,
            defaults={'name': name, 'is_active': True},
        )

    for verification in UserVerification.objects.all().only('id', 'document_type'):
        if not verification.document_type:
            continue
        document_type = VerificationDocumentType.objects.filter(
            code=verification.document_type
        ).first()
        if document_type:
            UserVerification.objects.filter(id=verification.id).update(
                document_type_ref_id=document_type.id
            )


def unseed_document_types(apps, schema_editor):
    VerificationDocumentType = apps.get_model('verification', 'VerificationDocumentType')
    VerificationDocumentType.objects.filter(code__in=[code for code, _ in DOCUMENT_TYPES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('verification', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='VerificationDocumentType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(max_length=32, unique=True)),
                ('name', models.CharField(max_length=120)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'verification_document_types',
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='userverification',
            name='document_type_ref',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='verifications',
                to='verification.verificationdocumenttype',
            ),
        ),
        migrations.RunPython(seed_document_types, unseed_document_types),
        migrations.RemoveField(
            model_name='userverification',
            name='document_type',
        ),
        migrations.RenameField(
            model_name='userverification',
            old_name='document_type_ref',
            new_name='document_type',
        ),
        migrations.AlterField(
            model_name='userverification',
            name='document_type',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='verifications',
                to='verification.verificationdocumenttype',
            ),
        ),
    ]
