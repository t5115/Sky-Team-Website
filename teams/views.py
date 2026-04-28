from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from departments.models import Department

from .forms import TeamDependencyForm
from .models import Team, TeamDependency, TeamMembership


def superuser_required(user):
    """
    Return True only for logged-in superusers.

    This function is reused by dependency write actions because only admins
    should be able to change organisational relationships between teams.
    """
    return user.is_authenticated and user.is_superuser


@login_required
def team_list(request):
    """
    Display all teams with filtering, sorting, member counts, and dependency counts.
    """
    search_query = request.GET.get('search', '').strip()
    department_filter = request.GET.get('department', '').strip()
    sort_by = request.GET.get('sort', 'name')

    # Prefetch active memberships with their person in one query.
    # This avoids making one database query for every team card.
    active_memberships = Prefetch(
        'memberships',
        queryset=TeamMembership.objects.filter(
            left_at__isnull=True
        ).select_related('person').order_by('joined_at'),
        to_attr='active_memberships',
    )

    teams = (
        Team.objects
        .prefetch_related(active_memberships, 'dependencies', 'dependent_teams')
        .select_related('team_leader', 'department')
    )

    if search_query:
        teams = teams.filter(name__icontains=search_query)

    if department_filter:
        teams = teams.filter(department__name=department_filter)

    if sort_by == 'repos':
        pass  # no repository count on Team yet — keep default ordering
    elif sort_by == 'members':
        teams = sorted(teams, key=lambda t: len(t.active_memberships), reverse=True)
    elif sort_by == 'dependencies':
        teams = sorted(teams, key=lambda t: t.dependency_count, reverse=True)
    else:
        teams = teams.order_by('name')

    departments = Department.objects.values_list('name', flat=True).order_by('name')

    context = {
        'teams': teams,
        'departments': departments,
        'search_query': search_query,
        'department_filter': department_filter,
        'sort_by': sort_by,
    }
    return render(request, 'teams/team_list.html', context)


@login_required
def team_dependency_overview(request):
    """
    Show a read-only overview of all team dependencies.

    This page helps users understand the organisation structure without needing
    permission to edit it.
    """
    teams = (
        Team.objects
        .select_related('team_leader', 'department')
        .prefetch_related(
            Prefetch(
                'dependencies',
                queryset=TeamDependency.objects.select_related('required_team'),
            ),
            Prefetch(
                'dependent_teams',
                queryset=TeamDependency.objects.select_related('dependent_team'),
            ),
        )
        .order_by('name')
    )

    context = {
        'teams': teams,
    }
    return render(request, 'teams/team_dependency_overview.html', context)


@login_required
def manage_team_dependencies(request, pk):
    """
    Display one team's dependency page.

    All logged-in users can view the page. Only superusers can submit changes.
    """
    team = get_object_or_404(Team.objects.select_related('team_leader', 'department'), pk=pk)

    dependencies = TeamDependency.objects.filter(
        dependent_team=team
    ).select_related('required_team').order_by('required_team__name')

    dependent_teams = TeamDependency.objects.filter(
        required_team=team
    ).select_related('dependent_team').order_by('dependent_team__name')

    if request.method == 'POST':
        if not request.user.is_superuser:
            messages.error(request, 'Only superusers can change team dependencies.')
            return redirect('teams:manage_team_dependencies', pk=team.pk)

        form = TeamDependencyForm(request.POST, team=team)

        if form.is_valid():
            form.save()
            messages.success(request, 'Team dependency added successfully.')
            return redirect('teams:manage_team_dependencies', pk=team.pk)
    else:
        form = TeamDependencyForm(team=team)

    context = {
        'team': team,
        'dependencies': dependencies,
        'dependent_teams': dependent_teams,
        'form': form,
    }
    return render(request, 'teams/team_dependency_manage.html', context)


@require_POST
@login_required
@user_passes_test(superuser_required)
def delete_team_dependency(request, pk, dependency_id):
    """
    Delete one dependency from a team.

    The URL contains both the team id and dependency id so we can safely confirm
    that the dependency belongs to the team being managed before deleting it.
    """
    team = get_object_or_404(Team, pk=pk)
    dependency = get_object_or_404(
        TeamDependency,
        pk=dependency_id,
        dependent_team=team,
    )

    dependency.delete()
    messages.success(request, 'Team dependency removed successfully.')
    return redirect('teams:manage_team_dependencies', pk=team.pk)
