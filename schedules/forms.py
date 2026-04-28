from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from people.models import Person

from .models import Meeting, MeetingParticipant
from .services import find_meeting_conflicts, get_schedulable_teams_for_user, get_team_people


class MeetingForm(forms.ModelForm):
    """Form used to create and update team meetings."""

    invite_whole_team = forms.BooleanField(
        required=False,
        initial=True,
        label='Invite all active team members',
        help_text='When selected, everyone currently in the selected team is invited automatically.',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    participants = forms.ModelMultipleChoiceField(
        queryset=Person.objects.none(),
        required=False,
        label='Extra participants',
        help_text='Use this when you want to invite specific people instead of, or in addition to, the full team.',
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '8'}),
    )

    class Meta:
        model = Meeting
        fields = [
            'team',
            'title',
            'description',
            'location',
            'meeting_link',
            'start_datetime',
            'end_datetime',
            'visibility',
            'invite_whole_team',
            'participants',
        ]
        widgets = {
            'team': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Example: Sprint planning, architecture review, daily stand-up',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Add agenda, goals, preparation notes, or useful context.',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Example: Meeting Room 2A or Microsoft Teams',
            }),
            'meeting_link': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://...',
            }),
            'start_datetime': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }, format='%Y-%m-%dT%H:%M'),
            'end_datetime': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }, format='%Y-%m-%dT%H:%M'),
            'visibility': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        self.fields['team'].queryset = get_schedulable_teams_for_user(user)
        self.fields['start_datetime'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['end_datetime'].input_formats = ['%Y-%m-%dT%H:%M']

        selected_team = self._get_selected_team()
        if selected_team:
            self.fields['participants'].queryset = Person.objects.filter(
                is_active=True
            ).order_by('first_name', 'last_name')
        else:
            self.fields['participants'].queryset = Person.objects.filter(
                is_active=True
            ).order_by('first_name', 'last_name')

        if self.instance and self.instance.pk:
            self.fields['participants'].initial = self.instance.participants.all()
            self.fields['invite_whole_team'].initial = False

    def _get_selected_team(self):
        if self.is_bound:
            team_id = self.data.get(self.add_prefix('team'))
            if team_id:
                try:
                    return self.fields['team'].queryset.get(pk=team_id)
                except Exception:
                    return None
        return self.instance.team if self.instance and self.instance.pk else None

    def clean(self):
        cleaned_data = super().clean()
        team = cleaned_data.get('team')
        start_datetime = cleaned_data.get('start_datetime')
        end_datetime = cleaned_data.get('end_datetime')

        if start_datetime and start_datetime < timezone.now() and not self.instance.pk:
            self.add_error('start_datetime', 'You cannot schedule a new meeting in the past.')

        if team and start_datetime and end_datetime:
            conflicts = find_meeting_conflicts(
                team=team,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                ignore_meeting=self.instance,
            )
            if conflicts.exists():
                conflict = conflicts.first()
                local_start = timezone.localtime(conflict.start_datetime).strftime('%d %b %Y, %H:%M')
                local_end = timezone.localtime(conflict.end_datetime).strftime('%H:%M')
                raise ValidationError(
                    f'This team already has a meeting at {local_start} - {local_end}: {conflict.title}.'
                )

        return cleaned_data

    def save(self, commit=True):
        meeting = super().save(commit=False)

        if commit:
            meeting.save()
            self.save_participants(meeting)

        return meeting

    def save_participants(self, meeting):
        """Synchronise participant rows after the meeting is saved."""
        selected_people = set(self.cleaned_data.get('participants', []))

        if self.cleaned_data.get('invite_whole_team'):
            selected_people.update(get_team_people(meeting.team))

        if meeting.organizer:
            selected_people.add(meeting.organizer)

        MeetingParticipant.objects.filter(meeting=meeting).exclude(
            person__in=selected_people
        ).delete()

        for person in selected_people:
            MeetingParticipant.objects.get_or_create(
                meeting=meeting,
                person=person,
            )
