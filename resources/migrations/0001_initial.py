# Generated for the Sky Team Website resources feature.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('teams', '0003_teamdependency'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeamResource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Short clear name, for example Backend API Repository.', max_length=150)),
                ('resource_type', models.CharField(choices=[('repository', 'Repository'), ('service', 'Service'), ('contact_channel', 'Contact Channel')], help_text='The kind of team resource.', max_length=30)),
                ('url', models.URLField(blank=True, help_text='Optional link to the resource, repository, service, or channel.')),
                ('contact_detail', models.CharField(blank=True, help_text='Optional channel name, email address, or internal contact reference.', max_length=200)),
                ('description', models.TextField(blank=True, help_text='Short explanation of how this resource is used.')),
                ('is_active', models.BooleanField(default=True, help_text='Inactive resources are hidden from normal use but kept for history.')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('team', models.ForeignKey(help_text='The team that owns or maintains this resource.', on_delete=django.db.models.deletion.CASCADE, related_name='resources', to='teams.team')),
            ],
            options={
                'verbose_name': 'Team resource',
                'verbose_name_plural': 'Team resources',
                'ordering': ['team__name', 'resource_type', 'name'],
            },
        ),
        migrations.AddConstraint(
            model_name='teamresource',
            constraint=models.UniqueConstraint(fields=('team', 'resource_type', 'name'), name='unique_team_resource_name_per_type'),
        ),
    ]
