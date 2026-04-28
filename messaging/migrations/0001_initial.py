# Generated manually for the production-grade messaging feature.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('teams', '0003_teamdependency'),
    ]

    operations = [
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=180)),
                ('conversation_type', models.CharField(choices=[('direct', 'Direct message'), ('group', 'Group chat'), ('team', 'Team chat')], default='direct', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_conversations', to=settings.AUTH_USER_MODEL)),
                ('team', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='conversations', to='teams.team')),
            ],
            options={
                'ordering': ['-updated_at'],
                'indexes': [models.Index(fields=['conversation_type', 'updated_at'], name='messaging_c_convers_651607_idx'), models.Index(fields=['team', 'updated_at'], name='messaging_c_team_id_5e8197_idx')],
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.TextField(max_length=5000)),
                ('attachment_url', models.URLField(blank=True)),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
                ('edited_at', models.DateTimeField(blank=True, null=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='messaging.conversation')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sent_messages', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['sent_at'],
                'indexes': [models.Index(fields=['conversation', 'sent_at'], name='messaging_m_convers_e0d957_idx'), models.Index(fields=['sender', 'sent_at'], name='messaging_m_sender__8c6c8d_idx')],
            },
        ),
        migrations.CreateModel(
            name='ConversationParticipant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('member', 'Member'), ('admin', 'Admin')], default='member', max_length=20)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('left_at', models.DateTimeField(blank=True, null=True)),
                ('last_read_at', models.DateTimeField(blank=True, null=True)),
                ('is_archived', models.BooleanField(default=False)),
                ('is_muted', models.BooleanField(default=False)),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participant_links', to='messaging.conversation')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conversation_links', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['joined_at'],
                'indexes': [models.Index(fields=['user', 'is_archived', 'left_at'], name='messaging_c_user_id_1d7d6a_idx'), models.Index(fields=['conversation', 'left_at'], name='messaging_c_convers_8673c3_idx')],
                'constraints': [models.UniqueConstraint(fields=('conversation', 'user'), name='unique_conversation_user_participant')],
            },
        ),
        migrations.CreateModel(
            name='MessageReadReceipt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('read_at', models.DateTimeField(auto_now_add=True)),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='read_receipts', to='messaging.message')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='message_read_receipts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'indexes': [models.Index(fields=['user', 'read_at'], name='messaging_m_user_id_5f3850_idx')],
                'constraints': [models.UniqueConstraint(fields=('message', 'user'), name='unique_message_read_receipt')],
            },
        ),
    ]
