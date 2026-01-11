# Generated manually for location tracking fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0002_add_payment_method_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='last_location',
            field=models.JSONField(
                blank=True,
                help_text="Last known location {'lat': ..., 'lng': ...}",
                null=True
            ),
        ),
        migrations.AddField(
            model_name='booking',
            name='last_location_time',
            field=models.DateTimeField(
                blank=True,
                help_text='Timestamp of last location update',
                null=True
            ),
        ),
    ]
