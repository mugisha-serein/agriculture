"""Add document type requirements and document expiry date."""

from django.db import migrations, models


REQUIREMENTS = {
    'national_id': {'requires_back_image': True, 'requires_expiry_date': False},
    'passport': {'requires_back_image': False, 'requires_expiry_date': True},
    'driver_license': {'requires_back_image': True, 'requires_expiry_date': True},
    'business_registration': {'requires_back_image': False, 'requires_expiry_date': False},
}


def seed_requirements(apps, schema_editor):
    VerificationDocumentType = apps.get_model('verification', 'VerificationDocumentType')
    for code, flags in REQUIREMENTS.items():
        VerificationDocumentType.objects.filter(code=code).update(**flags)


class Migration(migrations.Migration):

    dependencies = [
        ('verification', '0004_verification_documents'),
    ]

    operations = [
        migrations.AddField(
            model_name='verificationdocumenttype',
            name='requires_back_image',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='verificationdocumenttype',
            name='requires_expiry_date',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='verificationdocument',
            name='expiry_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.RunPython(seed_requirements, migrations.RunPython.noop),
    ]
