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
        """Active TeamMembership records for this team."""
        return self.memberships.filter(left_at__isnull=True).select_related('person')

    @property
    def member_count(self):
        return self.memberships.filter(left_at__isnull=True).count()

    @property
    def leader_name(self):
        if self.team_leader:
            return f"{self.team_leader.first_name} {self.team_leader.last_name}"
        return ""

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
