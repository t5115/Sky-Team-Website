from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from .models import Team, TeamMembership


@login_required
def team_list(request):
    search_query = request.GET.get('search', '').strip()
    department_filter = request.GET.get('department', '').strip()
    sort_by = request.GET.get('sort', 'name')

    # Prefetch active memberships with their person in one query
    active_memberships = Prefetch(
        'memberships',
        queryset=TeamMembership.objects.filter(
            left_at__isnull=True
        ).select_related('person').order_by('joined_at'),
        to_attr='active_memberships',
    )

    teams = Team.objects.prefetch_related(active_memberships).select_related('team_leader')

    if search_query:
        teams = teams.filter(name__icontains=search_query)

    if department_filter:
        teams = teams.filter(department__name=department_filter)

    if sort_by == 'repos':
        pass  # no repo count on Team yet — keep default ordering
    elif sort_by == 'members':
        teams = sorted(teams, key=lambda t: len(t.active_memberships), reverse=True)
    else:
        teams = teams.order_by('name')

    from departments.models import Department
    departments = Department.objects.values_list('name', flat=True).order_by('name')

    context = {
        'teams': teams,
        'departments': departments,
        'search_query': search_query,
        'department_filter': department_filter,
        'sort_by': sort_by,
    }
    return render(request, 'teams/team_list.html', context)
