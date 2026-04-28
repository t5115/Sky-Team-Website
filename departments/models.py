from django.db import models


class Department(models.Model):
    # ERD: department_head_person_id (FK) → Person
    department_head = models.ForeignKey(
        'people.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_departments',
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def team_count(self):
        return self.department_teams.count()

    @property
    def head_name(self):
        if self.department_head:
            return f"{self.department_head.first_name} {self.department_head.last_name}"
        return ""

    class Meta:
        ordering = ['name']
