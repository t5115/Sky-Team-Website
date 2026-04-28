# Generated manually for the schedules feature.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('people', '0001_initial'),
        ('teams', '0003_teamdependency'),
    ]

    operations = [
        migrations.CreateModel(
            name='Meeting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('location', models.CharField(blank=True, help_text='Physical room or online meeting location.', max_length=200)),
                ('meeting_link', models.URLField(blank=True)),
                ('start_datetime', models.DateTimeField()),
                ('end_datetime', models.DateTimeField()),
                ('status', models.CharField(choices=[('scheduled', 'Scheduled'), ('cancelled', 'Cancelled'), ('completed', 'Completed')], default='scheduled', max_length=20)),
                ('visibility', models.CharField(choices=[('team_only', 'Team only'), ('organisation', 'Organisation')], default='team_only', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_meetings', to=settings.AUTH_USER_MODEL)),
                ('organizer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='organized_meetings', to='people.person')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='meetings', to='teams.team')),
            ],
            options={
                'ordering': ['start_datetime', 'title'],
            },
        ),
        migrations.CreateModel(
            name='MeetingParticipant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('response_status', models.CharField(choices=[('invited', 'Invited'), ('accepted', 'Accepted'), ('declined', 'Declined'), ('tentative', 'Tentative')], default='invited', max_length=20)),
                ('invited_at', models.DateTimeField(auto_now_add=True)),
                ('responded_at', models.DateTimeField(blank=True, null=True)),
                ('meeting', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participant_links', to='schedules.meeting')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='meeting_participations', to='people.person')),
            ],
            options={
                'ordering': ['person__first_name', 'person__last_name'],
            },
        ),
        migrations.AddField(
            model_name='meeting',
            name='participants',
            field=models.ManyToManyField(blank=True, related_name='meetings', through='schedules.MeetingParticipant', to='people.person'),
        ),
        migrations.AddIndex(
            model_name='meeting',
            index=models.Index(fields=['team', 'start_datetime'], name='schedules_m_team_id_9f0a4d_idx'),
        ),
        migrations.AddIndex(
            model_name='meeting',
            index=models.Index(fields=['status', 'start_datetime'], name='schedules_m_status_9dc78d_idx'),
        ),
        migrations.AddConstraint(
            model_name='meetingparticipant',
            constraint=models.UniqueConstraint(fields=('meeting', 'person'), name='unique_meeting_participant'),
        ),
    ]
