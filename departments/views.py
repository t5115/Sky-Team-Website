from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from .models import Department
from teams.models import Team


@login_required
def department_list(request):
    search_query = request.GET.get('search', '').strip()
    sort_by = request.GET.get('sort', 'name')

    teams_prefetch = Prefetch(
        'department_teams',
        queryset=Team.objects.select_related('team_leader').order_by('name'),
        to_attr='prefetched_teams',
    )

    departments = Department.objects.prefetch_related(teams_prefetch).select_related('department_head')

    if search_query:
        departments = departments.filter(name__icontains=search_query)

    if sort_by == 'teams':
        departments = sorted(list(departments), key=lambda d: len(d.prefetched_teams), reverse=True)
    else:
        departments = list(departments.order_by('name'))

    context = {
        'departments': departments,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    return render(request, 'departments/department_list.html', context)
