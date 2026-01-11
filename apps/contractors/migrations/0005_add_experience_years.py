# Generated migration for adding experience_years field to ContractorProfile

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contractors', '0004_add_site_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='contractorprofile',
            name='experience_years',
            field=models.IntegerField(default=0),
        ),
    ]
