from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Meeting(models.Model):
    """
    A scheduled meeting for a team.

    Production-style rules:
    - Every meeting belongs to one team.
    - A meeting has an authenticated creator for audit history.
    - A meeting can optionally be linked to a Person organizer profile.
    - Start time must be before end time.
    - Cancelled meetings are kept for history instead of being deleted.
    """

    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        CANCELLED = 'cancelled', 'Cancelled'
        COMPLETED = 'completed', 'Completed'

    class Visibility(models.TextChoices):
        TEAM_ONLY = 'team_only', 'Team only'
        ORGANISATION = 'organisation', 'Organisation'

    team = models.ForeignKey(
        'teams.Team',
        on_delete=models.CASCADE,
        related_name='meetings',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_meetings',
    )
    organizer = models.ForeignKey(
        'people.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='organized_meetings',
    )
    participants = models.ManyToManyField(
        'people.Person',
        through='MeetingParticipant',
        related_name='meetings',
        blank=True,
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.CharField(
        max_length=200,
        blank=True,
        help_text='Physical room or online meeting location.',
    )
    meeting_link = models.URLField(blank=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
    )
    visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.TEAM_ONLY,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_datetime', 'title']
        indexes = [
            models.Index(fields=['team', 'start_datetime']),
            models.Index(fields=['status', 'start_datetime']),
        ]

    def __str__(self):
        return f'{self.title} - {self.team.name}'

    @property
    def is_cancelled(self):
        return self.status == self.Status.CANCELLED

    @property
    def is_past(self):
        return self.end_datetime < timezone.now()

    def clean(self):
        super().clean()
        errors = {}

        if self.title is not None:
            self.title = self.title.strip()
        if self.description is not None:
            self.description = self.description.strip()
        if self.location is not None:
            self.location = self.location.strip()
        if self.meeting_link is not None:
            self.meeting_link = self.meeting_link.strip()

        if not self.title:
            errors['title'] = 'Meeting title is required.'

        if self.start_datetime and self.end_datetime:
            if self.end_datetime <= self.start_datetime:
                errors['end_datetime'] = 'End time must be after the start time.'

        if self.meeting_link and not self.meeting_link.startswith(('http://', 'https://')):
            errors['meeting_link'] = 'Meeting link must start with http:// or https://.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class MeetingParticipant(models.Model):
    """
    Junction table between Meeting and Person.

    This gives us more information than a normal ManyToMany table, such as each
    participant's response status and the time they were invited.
    """

    class ResponseStatus(models.TextChoices):
        INVITED = 'invited', 'Invited'
        ACCEPTED = 'accepted', 'Accepted'
        DECLINED = 'declined', 'Declined'
        TENTATIVE = 'tentative', 'Tentative'

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='participant_links',
    )
    person = models.ForeignKey(
        'people.Person',
        on_delete=models.CASCADE,
        related_name='meeting_participations',
    )
    response_status = models.CharField(
        max_length=20,
        choices=ResponseStatus.choices,
        default=ResponseStatus.INVITED,
    )
    invited_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['meeting', 'person'],
                name='unique_meeting_participant',
            ),
        ]
        ordering = ['person__first_name', 'person__last_name']

    def __str__(self):
        return f'{self.person} invited to {self.meeting}'
