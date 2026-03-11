"""Refactor user verification fields for lifecycle tracking."""

import django.utils.timezone
from django.db import migrations, models


def populate_status_changed_at(apps, schema_editor):
    UserVerification = apps.get_model('verification', 'UserVerification')
    for verification in UserVerification.objects.all().only('id', 'submitted_at', 'reviewed_at'):
        status_changed_at = verification.reviewed_at or verification.submitted_at
        UserVerification.objects.filter(id=verification.id).update(
            status_changed_at=status_changed_at
        )


class Migration(migrations.Migration):

    dependencies = [
        ('verification', '0002_document_types'),
    ]

    operations = [
        migrations.AddField(
            model_name='userverification',
            name='status_changed_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.RenameField(
            model_name='userverification',
            old_name='admin_notes',
            new_name='review_notes',
        ),
        migrations.RunPython(populate_status_changed_at, migrations.RunPython.noop),
    ]
