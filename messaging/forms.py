from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from teams.models import Team

from .models import Message
from .services import get_active_team_users

User = get_user_model()


class ConversationStartForm(forms.Form):
    mode = forms.ChoiceField(
        choices=[('direct', 'Direct message'), ('group', 'Group chat'), ('team', 'Team chat')],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    title = forms.CharField(
        required=False,
        max_length=180,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Required for group chats'}),
    )
    recipient = forms.ModelChoiceField(
        required=False,
        queryset=User.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Choose one user for a direct message.',
    )
    participants = forms.ModelMultipleChoiceField(
        required=False,
        queryset=User.objects.none(),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '8'}),
        help_text='Choose two or more people for a group chat.',
    )
    team = forms.ModelChoiceField(
        required=False,
        queryset=Team.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Team chat automatically includes active team members who have user accounts.',
    )
    first_message = forms.CharField(
        required=True,
        max_length=5000,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Write the first message...'}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        users = User.objects.filter(is_active=True).exclude(pk=user.pk).order_by('username')
        self.fields['recipient'].queryset = users
        self.fields['participants'].queryset = users
        self.fields['team'].queryset = Team.objects.filter(status='active').order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        mode = cleaned_data.get('mode')
        title = (cleaned_data.get('title') or '').strip()
        recipient = cleaned_data.get('recipient')
        participants = cleaned_data.get('participants')
        team = cleaned_data.get('team')

        if mode == 'direct':
            if not recipient:
                self.add_error('recipient', 'Choose the user you want to message.')
        elif mode == 'group':
            if not title:
                self.add_error('title', 'A group chat needs a clear title.')
            if not participants or participants.count() < 1:
                self.add_error('participants', 'Choose at least one other participant.')
        elif mode == 'team':
            if not team:
                self.add_error('team', 'Choose the team for this chat.')
            elif not get_active_team_users(team).exclude(pk=self.user.pk).exists():
                self.add_error('team', 'This team has no other active linked user accounts yet.')
        else:
            raise ValidationError('Invalid conversation type.')

        cleaned_data['title'] = title
        return cleaned_data


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['body', 'attachment_url']
        widgets = {
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Type your message...'}),
            'attachment_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Optional attachment link: https://...'}),
        }
