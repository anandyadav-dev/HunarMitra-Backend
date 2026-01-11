# Generated manually - adds event_type field to Event model
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0001_initial'),
    ]

    operations = [
        # Rename 'name' field to 'event_type'
        migrations.RenameField(
            model_name='event',
            old_name='name',
            new_name='event_type',
        ),
        # Alter field to match new definition
        migrations.AlterField(
            model_name='event',
            name='event_type',
            field=models.CharField(db_index=True, help_text='Type of event', max_length=50),
        ),
        # Remove old indexes that use 'name'
        migrations.RemoveIndex(
            model_name='event',
            name='analytics_e_name_4a8b2c_idx',
        ),
    ]
