from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('logistics', '0002_deliverypartner_alter_shipment_status_deliveryroute_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='shipmenttrackingevent',
            old_name='latitude',
            new_name='lat',
        ),
        migrations.RenameField(
            model_name='shipmenttrackingevent',
            old_name='longitude',
            new_name='lng',
        ),
        migrations.RenameField(
            model_name='shipmenttrackingevent',
            old_name='event_timestamp',
            new_name='timestamp',
        ),
    ]
