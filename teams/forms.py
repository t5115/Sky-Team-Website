from django import forms

from .models import Team, TeamDependency


class TeamDependencyForm(forms.ModelForm):
    """
    Form used by superusers to add a dependency for one selected team.

    The selected team is passed into the form from the view. This allows the
    form to hide invalid choices, such as the team depending on itself or a
    dependency that already exists.
    """

    class Meta:
        model = TeamDependency
        fields = ['required_team', 'reason']
        widgets = {
            'required_team': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional: explain why this dependency exists.',
            }),
        }
        labels = {
            'required_team': 'Depends on team',
            'reason': 'Reason',
        }

    def __init__(self, *args, team=None, **kwargs):
        """
        Store the current team and restrict the dropdown to valid teams only.
        """
        super().__init__(*args, **kwargs)
        self.team = team

        queryset = Team.objects.all().order_by('name')

        if self.team:
            existing_required_team_ids = TeamDependency.objects.filter(
                dependent_team=self.team
            ).values_list('required_team_id', flat=True)

            queryset = queryset.exclude(pk=self.team.pk).exclude(
                pk__in=existing_required_team_ids
            )

        self.fields['required_team'].queryset = queryset

    def save(self, commit=True):
        """
        Attach the current team as dependent_team before saving.
        """
        dependency = super().save(commit=False)
        dependency.dependent_team = self.team

        if commit:
            dependency.save()

        return dependency
