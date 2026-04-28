from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Prefetch
from django.shortcuts import render

from departments.models import Department
from teams.models import Team, TeamDependency, TeamMembership
from resources.models import TeamResource


def home(request):
    return render(request, 'core/core.html')


@login_required
def organisation_diagram(request):
    """
    Display a read-only organisation diagram.

    The diagram summarises the organisation using the existing relational data:
    Department → Team → Team leader / members / dependencies.

    This view deliberately does not create, edit, or delete data. It is a safe
    summary page for normal users and administrators.
    """
    search_query = request.GET.get('search', '').strip()
    department_id = request.GET.get('department', '').strip()
    status_filter = request.GET.get('status', '').strip()

    # Active memberships are prefetched into a custom attribute so the template
    # can display team member counts without causing one database query per team.
    active_memberships = Prefetch(
        'memberships',
        queryset=TeamMembership.objects.filter(
            left_at__isnull=True
        ).select_related('person').order_by('person__first_name', 'person__last_name'),
        to_attr='diagram_active_memberships',
    )

    # Team dependencies are also prefetched to avoid N+1 queries in the diagram.
    team_queryset = (
        Team.objects
        .select_related('team_leader', 'department')
        .prefetch_related(
            active_memberships,
            Prefetch(
                'dependencies',
                queryset=TeamDependency.objects.select_related('required_team').order_by('required_team__name'),
                to_attr='diagram_dependencies',
            ),
            Prefetch(
                'dependent_teams',
                queryset=TeamDependency.objects.select_related('dependent_team').order_by('dependent_team__name'),
                to_attr='diagram_dependent_teams',
            ),
            # Active team resources are prefetched so the diagram can summarise
            # services, repositories, and contact channels without extra queries.
            Prefetch(
                'resources',
                queryset=TeamResource.objects.filter(is_active=True).order_by('resource_type', 'name'),
                to_attr='diagram_resources',
            ),
        )
        .order_by('name')
    )

    if status_filter:
        team_queryset = team_queryset.filter(status=status_filter)

    if search_query:
        team_queryset = team_queryset.filter(
            models.Q(name__icontains=search_query)
            | models.Q(purpose_description__icontains=search_query)
            | models.Q(team_leader__first_name__icontains=search_query)
            | models.Q(team_leader__last_name__icontains=search_query)
            | models.Q(department__name__icontains=search_query)
        ).distinct()

    departments = (
        Department.objects
        .select_related('department_head')
        .prefetch_related(
            Prefetch(
                'department_teams',
                queryset=team_queryset,
                to_attr='diagram_teams',
            )
        )
        .order_by('name')
    )

    if department_id:
        departments = departments.filter(pk=department_id)

    # Convert to a list so we can safely calculate totals from the prefetched data.
    departments = list(departments)

    # If a search is active, hide departments that have no matching teams and do
    # not match the department name. This keeps the diagram focused and readable.
    if search_query:
        departments = [
            department for department in departments
            if department.diagram_teams or search_query.lower() in department.name.lower()
        ]

    total_departments = len(departments)
    total_teams = sum(len(department.diagram_teams) for department in departments)
    total_memberships = sum(
        len(team.diagram_active_memberships)
        for department in departments
        for team in department.diagram_teams
    )
    total_dependencies = sum(
        len(team.diagram_dependencies)
        for department in departments
        for team in department.diagram_teams
    )
    total_resources = sum(
        len(team.diagram_resources)
        for department in departments
        for team in department.diagram_teams
    )

    context = {
        'departments': departments,
        'all_departments': Department.objects.order_by('name'),
        'status_choices': Team.STATUS_CHOICES,
        'search_query': search_query,
        'department_id': department_id,
        'status_filter': status_filter,
        'total_departments': total_departments,
        'total_teams': total_teams,
        'total_memberships': total_memberships,
        'total_dependencies': total_dependencies,
        'total_resources': total_resources,
    }
    return render(request, 'core/organisation_diagram.html', context)
