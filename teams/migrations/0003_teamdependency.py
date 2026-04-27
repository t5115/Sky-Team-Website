# Generated manually for the Team Dependency feature.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teams', '0002_team_department'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeamDependency',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('dependent_team', models.ForeignKey(help_text='The team that depends on another team.', on_delete=django.db.models.deletion.CASCADE, related_name='dependencies', to='teams.team')),
                ('required_team', models.ForeignKey(help_text='The team that is required by another team.', on_delete=django.db.models.deletion.CASCADE, related_name='dependent_teams', to='teams.team')),
            ],
            options={
                'verbose_name': 'Team dependency',
                'verbose_name_plural': 'Team dependencies',
                'ordering': ['dependent_team__name', 'required_team__name'],
            },
        ),
        migrations.AddConstraint(
            model_name='teamdependency',
            constraint=models.UniqueConstraint(fields=('dependent_team', 'required_team'), name='unique_team_dependency'),
        ),
        migrations.AddConstraint(
            model_name='teamdependency',
            constraint=models.CheckConstraint(condition=models.Q(('dependent_team', models.F('required_team')), _negated=True), name='prevent_team_self_dependency'),
        ),
    ]
