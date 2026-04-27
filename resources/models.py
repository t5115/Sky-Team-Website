from django.core.exceptions import ValidationError
from django.db import models

from teams.models import Team


class TeamResource(models.Model):
    """
    Stores resources that belong to a team.

    Business rule for the Sky project:
    - resources are owned by teams, not directly by departments;
    - a team can have many repositories, services, and contact channels;
    - each resource belongs to exactly one team.

    We keep one table because repositories, services, and contact channels share
    the same core information: team, name, URL/contact detail, description, and
    active status. The resource_type field separates them in the UI.
    """

    class ResourceType(models.TextChoices):
        REPOSITORY = 'repository', 'Repository'
        SERVICE = 'service', 'Service'
        CONTACT_CHANNEL = 'contact_channel', 'Contact Channel'

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='resources',
        help_text='The team that owns or maintains this resource.',
    )
    name = models.CharField(
        max_length=150,
        help_text='Short clear name, for example Backend API Repository.',
    )
    resource_type = models.CharField(
        max_length=30,
        choices=ResourceType.choices,
        help_text='The kind of team resource.',
    )
    url = models.URLField(
        blank=True,
        help_text='Optional link to the resource, repository, service, or channel.',
    )
    contact_detail = models.CharField(
        max_length=200,
        blank=True,
        help_text='Optional channel name, email address, or internal contact reference.',
    )
    description = models.TextField(
        blank=True,
        help_text='Short explanation of how this resource is used.',
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Inactive resources are hidden from normal use but kept for history.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['team__name', 'resource_type', 'name']
        constraints = [
            # Prevent the same team from having duplicated resources with the
            # same name and type. Example: two active-looking "Backend Repo"
            # rows for the Backend team would confuse users.
            models.UniqueConstraint(
                fields=['team', 'resource_type', 'name'],
                name='unique_team_resource_name_per_type',
            ),
        ]
        verbose_name = 'Team resource'
        verbose_name_plural = 'Team resources'

    def __str__(self):
        return f'{self.name} - {self.team.name}'

    def clean(self):
        """
        Enforce resource business rules before saving.

        Repository resources must have a URL because users need a direct link to
        the repo. Contact channels are more flexible: they can be stored as a URL
        or as a contact detail such as a Teams channel name or email address.
        """
        super().clean()

        errors = {}

        # Normalize user-entered strings to avoid accidental duplicates caused
        # by leading/trailing spaces.
        if self.name is not None:
            self.name = self.name.strip()
        if self.url is not None:
            self.url = self.url.strip()
        if self.contact_detail is not None:
            self.contact_detail = self.contact_detail.strip()
        if self.description is not None:
            self.description = self.description.strip()

        if not self.name:
            errors['name'] = 'Resource name is required.'

        if self.resource_type == self.ResourceType.REPOSITORY and not self.url:
            errors['url'] = 'A repository resource must have a URL.'

        if self.resource_type == self.ResourceType.CONTACT_CHANNEL:
            if not self.url and not self.contact_detail:
                errors['contact_detail'] = 'A contact channel needs either a URL or contact detail.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """
        Run validation on every save, not only when a ModelForm is used.
        """
        self.full_clean()
        super().save(*args, **kwargs)
