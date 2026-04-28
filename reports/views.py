import csv

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from departments.models import Department
from people.models import Person
from resources.models import TeamResource
from teams.models import Team, TeamDependency, TeamMembership


def _build_organization_report_data():
    """
    Build all report numbers in one place so the HTML page and CSV download use
    the same logic.

    The report is read-only. It does not create, update, or delete any database
    records. It simply summarises the organisation data already stored in the
    Departments, Teams, People, TeamMembership, TeamDependency, and TeamResource
    tables.
    """

    departments = (
        Department.objects
        .select_related('department_head')
        .annotate(
            total_teams=Count('department_teams', distinct=True),
            active_teams=Count(
                'department_teams',
                filter=Q(department_teams__status='active'),
                distinct=True,
            ),
            inactive_teams=Count(
                'department_teams',
                filter=Q(department_teams__status='inactive'),
                distinct=True,
            ),
            archived_teams=Count(
                'department_teams',
                filter=Q(department_teams__status='archived'),
                distinct=True,
            ),
        )
        .order_by('name')
    )

    teams = (
        Team.objects
        .select_related('department', 'team_leader')
        .annotate(
            active_member_count=Count(
                'memberships',
                filter=Q(memberships__left_at__isnull=True),
                distinct=True,
            ),
            resource_count=Count(
                'resources',
                filter=Q(resources__is_active=True),
                distinct=True,
            ),
            depends_on_count=Count('dependencies', distinct=True),
            depended_on_by_count=Count('dependent_teams', distinct=True),
        )
        .order_by('department__name', 'name')
    )

    resource_breakdown = (
        TeamResource.objects
        .filter(is_active=True)
        .values('resource_type')
        .annotate(total=Count('id'))
        .order_by('resource_type')
    )

    team_status_breakdown = (
        Team.objects
        .values('status')
        .annotate(total=Count('id'))
        .order_by('status')
    )

    totals = {
        'departments': Department.objects.count(),
        'teams': Team.objects.count(),
        'active_teams': Team.objects.filter(status='active').count(),
        'inactive_teams': Team.objects.filter(status='inactive').count(),
        'archived_teams': Team.objects.filter(status='archived').count(),
        'people': Person.objects.count(),
        'active_people': Person.objects.filter(is_active=True).count(),
        'linked_profiles': Person.objects.filter(user__isnull=False).count(),
        'team_memberships': TeamMembership.objects.filter(left_at__isnull=True).count(),
        'team_dependencies': TeamDependency.objects.count(),
        'active_resources': TeamResource.objects.filter(is_active=True).count(),
    }

    generated_at = timezone.localtime(timezone.now())

    return {
        'departments': departments,
        'teams': teams,
        'resource_breakdown': resource_breakdown,
        'team_status_breakdown': team_status_breakdown,
        'totals': totals,
        'generated_at': generated_at,
    }


@login_required
def organization_report(request):
    """
    Display the organisation report in the dashboard.

    Users can see a summary of how the organisation is structured, including:
    - total departments;
    - total teams;
    - how many teams belong to each department;
    - team status distribution;
    - team members, dependencies, and active resources.
    """
    context = _build_organization_report_data()
    return render(request, 'reports/organization_report.html', context)


@login_required
def download_organization_report_csv(request):
    """
    Generate a CSV version of the organisation report.

    This gives users a simple report file they can download and share during
    analysis or the coursework demonstration.
    """
    data = _build_organization_report_data()
    generated_at = data['generated_at'].strftime('%Y-%m-%d %H:%M')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sky-organization-report.csv"'

    writer = csv.writer(response)

    writer.writerow(['Sky Organisation Report'])
    writer.writerow(['Generated at', generated_at])
    writer.writerow([])

    writer.writerow(['Overall Summary'])
    writer.writerow(['Metric', 'Value'])
    writer.writerow(['Departments', data['totals']['departments']])
    writer.writerow(['Teams', data['totals']['teams']])
    writer.writerow(['Active teams', data['totals']['active_teams']])
    writer.writerow(['Inactive teams', data['totals']['inactive_teams']])
    writer.writerow(['Archived teams', data['totals']['archived_teams']])
    writer.writerow(['People profiles', data['totals']['people']])
    writer.writerow(['Active people profiles', data['totals']['active_people']])
    writer.writerow(['Linked user profiles', data['totals']['linked_profiles']])
    writer.writerow(['Active team memberships', data['totals']['team_memberships']])
    writer.writerow(['Team dependencies', data['totals']['team_dependencies']])
    writer.writerow(['Active resources', data['totals']['active_resources']])
    writer.writerow([])

    writer.writerow(['Departments Breakdown'])
    writer.writerow(['Department', 'Department Head', 'Total Teams', 'Active Teams', 'Inactive Teams', 'Archived Teams'])
    for department in data['departments']:
        writer.writerow([
            department.name,
            department.head_name or 'Not assigned',
            department.total_teams,
            department.active_teams,
            department.inactive_teams,
            department.archived_teams,
        ])
    writer.writerow([])

    writer.writerow(['Teams Breakdown'])
    writer.writerow([
        'Team',
        'Department',
        'Leader',
        'Status',
        'Active Members',
        'Active Resources',
        'Depends On',
        'Depended On By',
    ])
    for team in data['teams']:
        writer.writerow([
            team.name,
            team.department.name if team.department else 'No department',
            team.leader_name or 'Not assigned',
            team.get_status_display(),
            team.active_member_count,
            team.resource_count,
            team.depends_on_count,
            team.depended_on_by_count,
        ])

    return response
