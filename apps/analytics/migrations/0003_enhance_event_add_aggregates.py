# Generated manually for analytics enhancement
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0002_rename_name_to_event_type'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Add new fields
        migrations.AddField(
            model_name='event',
            name='anonymous_id',
            field=models.CharField(blank=True, db_index=True, help_text='Client-generated anonymous ID for tracking', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='ip_address',
            field=models.GenericIPAddressField(blank=True, help_text='Client IP address', null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='user_agent',
            field=models.CharField(blank=True, help_text='Client user agent', max_length=500, null=True),
        ),
        # Update source field choices
        migrations.AlterField(
            model_name='event',
            name='source',
            field=models.CharField(choices=[('web', 'Web'), ('android', 'Android'), ('ios', 'iOS'), ('kiosk', 'Kiosk'), ('admin', 'Admin')], db_index=True, default='web', help_text='Event source platform', max_length=20),
        ),
        # Add new indexes
        migrations.AddIndex(
            model_name='event',
            index=models.Index(fields=['created_at'], name='analytics_created_idx'),
        ),
        migrations.AddIndex(
            model_name='event',
            index=models.Index(fields=['event_type', 'created_at'], name='analytics_type_created_idx'),
        ),
        migrations.AddIndex(
            model_name='event',
            index=models.Index(fields=['user', 'created_at'], name='analytics_user_created_idx'),
        ),
        migrations.AddIndex(
            model_name='event',
            index=models.Index(fields=['-created_at', 'event_type'], name='analytics_recent_type_idx'),
        ),
        # Create EventAggregateDaily model
        migrations.CreateModel(
            name='EventAggregateDaily',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(db_index=True, help_text='Aggregation date')),
                ('event_type', models.CharField(db_index=True, help_text='Event type', max_length=50)),
                ('source', models.CharField(blank=True, help_text='Source platform (optional)', max_length=20)),
                ('count', models.IntegerField(default=0, help_text='Number of events')),
                ('unique_users', models.IntegerField(default=0, help_text='Number of unique user IDs')),
                ('unique_anonymous', models.IntegerField(default=0, help_text='Number of unique anonymous IDs')),
                ('meta', models.JSONField(blank=True, default=dict, help_text='Additional aggregate metadata')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Daily Event Aggregate',
                'verbose_name_plural': 'Daily Event Aggregates',
                'db_table': 'analytics_event_aggregates_daily',
                'ordering': ['-date', 'event_type'],
            },
        ),
        migrations.AddIndex(
            model_name='eventaggregatedaily',
            index=models.Index(fields=['date', 'event_type'], name='agg_date_type_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='eventaggregatedaily',
            unique_together={('date', 'event_type', 'source')},
        ),
    ]
