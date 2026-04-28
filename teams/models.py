from django.core.exceptions import ValidationError
from django.db import models


class Team(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ]

    # ERD: team_leader_person_id (FK) → Person
    team_leader = models.ForeignKey(
        'people.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='led_teams',
    )
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='department_teams',
    )
    # ERD: department_id (FK) → Department (not yet built, use text for now)
    department_name = models.CharField(max_length=200, blank=True)

    name = models.CharField(max_length=200)
    purpose_description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def active_members(self):
        """Return the active TeamMembership records for this team."""
        return self.memberships.filter(left_at__isnull=True).select_related('person')

    @property
    def member_count(self):
        """Return the number of active members in the team."""
        return self.memberships.filter(left_at__isnull=True).count()

    @property
    def leader_name(self):
        """Return the full name of the team leader, or an empty string if none is assigned."""
        if self.team_leader:
            return f"{self.team_leader.first_name} {self.team_leader.last_name}"
        return ""

    @property
    def dependency_count(self):
        """
        Return how many teams this team depends on.

        Example:
        If Frontend depends on Backend and Design, this returns 2 for Frontend.
        """
        return self.dependencies.count()

    @property
    def dependent_team_count(self):
        """
        Return how many teams depend on this team.

        Example:
        If Frontend and Mobile depend on Backend, this returns 2 for Backend.
        """
        return self.dependent_teams.count()

    class Meta:
        ordering = ['name']


class TeamMembership(models.Model):
    """
    ERD: junction table between Team and Person.
    Fields: team_id, person_id, role, is_primary_contact, joined_at, left_at
    """
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    person = models.ForeignKey(
        'people.Person',
        on_delete=models.CASCADE,
        related_name='team_memberships',
    )
    role = models.CharField(max_length=100, blank=True)
    is_primary_contact = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('team', 'person')
        ordering = ['joined_at']

    def __str__(self):
        return f"{self.person} → {self.team}"


class TeamDependency(models.Model):
    """
    Associative table for dependencies between teams.

    This is a self-referencing relationship because both foreign keys point
    to the Team table.

    Example business meaning:
    - dependent_team = Frontend Team
    - required_team = Backend Team

    This means: "Frontend Team depends on Backend Team".
    """

    # The team that needs another team in order to do its work.
    dependent_team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='dependencies',
        help_text='The team that depends on another team.',
    )

    # The team that is required by the dependent team.
    required_team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='dependent_teams',
        help_text='The team that is required by another team.',
    )

    # Optional human explanation for why this dependency exists.
    reason = models.TextField(blank=True)

    # Audit timestamps for traceability.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Prevent duplicate rows such as Frontend -> Backend being saved twice.
        constraints = [
            models.UniqueConstraint(
                fields=['dependent_team', 'required_team'],
                name='unique_team_dependency',
            ),
            models.CheckConstraint(
                condition=~models.Q(dependent_team=models.F('required_team')),
                name='prevent_team_self_dependency',
            ),
        ]
        ordering = ['dependent_team__name', 'required_team__name']
        verbose_name = 'Team dependency'
        verbose_name_plural = 'Team dependencies'

    def __str__(self):
        return f"{self.dependent_team} depends on {self.required_team}"

    def _creates_cycle(self):
        """
        Return True if this dependency would create a circular dependency chain.

        Example of a cycle:
        - Frontend depends on Backend
        - Backend depends on Data
        - Data depends on Frontend  ← this is dangerous and confusing

        The method checks whether the required team already depends, directly
        or indirectly, on the dependent team.
        """
        if not self.dependent_team_id or not self.required_team_id:
            return False

        target_team_id = self.dependent_team_id
        teams_to_check = [self.required_team_id]
        checked_team_ids = set()

        while teams_to_check:
            current_team_id = teams_to_check.pop()

            if current_team_id == target_team_id:
                return True

            if current_team_id in checked_team_ids:
                continue

            checked_team_ids.add(current_team_id)

            next_team_ids = TeamDependency.objects.filter(
                dependent_team_id=current_team_id
            ).exclude(
                pk=self.pk
            ).values_list('required_team_id', flat=True)

            teams_to_check.extend(next_team_ids)

        return False

    def clean(self):
        """
        Validate dependency rules before saving.

        Rules:
        1. A team cannot depend on itself.
        2. The same dependency cannot be duplicated.
        3. Circular dependency chains are blocked.
        """
        super().clean()

        if self.dependent_team_id and self.required_team_id:
            if self.dependent_team_id == self.required_team_id:
                raise ValidationError('A team cannot depend on itself.')

            duplicate_exists = TeamDependency.objects.filter(
                dependent_team_id=self.dependent_team_id,
                required_team_id=self.required_team_id,
            ).exclude(pk=self.pk).exists()

            if duplicate_exists:
                raise ValidationError('This team dependency already exists.')

            if self._creates_cycle():
                raise ValidationError(
                    'This dependency would create a circular dependency chain.'
                )

    def save(self, *args, **kwargs):
        """
        Run model validation before saving.

        Django forms call validation automatically, but calling full_clean()
        here protects us if a dependency is created from the shell, admin,
        custom scripts, or future views.
        """
        self.full_clean()
        super().save(*args, **kwargs)
