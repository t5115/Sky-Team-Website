from datetime import date, timedelta

from django.db.models import Q
from django.utils import timezone

from people.models import Person
from teams.models import Team, TeamMembership

from .models import Meeting


def get_person_for_user(user):
    """Return the linked Person profile for a user, or None if not linked."""
    if not user.is_authenticated:
        return None
    return getattr(user, 'person_profile', None)


def get_schedulable_teams_for_user(user):
    """
    Return teams that the user is allowed to schedule meetings for.

    Superusers can schedule for every team. Normal users can schedule meetings
    for teams where their linked Person profile is an active member or leader.
    """
    teams = Team.objects.select_related('department', 'team_leader').filter(status='active')

    if user.is_superuser:
        return teams.order_by('name')

    person = get_person_for_user(user)
    if person is None:
        return Team.objects.none()

    member_team_ids = TeamMembership.objects.filter(
        person=person,
        left_at__isnull=True,
    ).values_list('team_id', flat=True)

    return teams.filter(
        Q(pk__in=member_team_ids) | Q(team_leader=person)
    ).distinct().order_by('name')


def user_can_manage_meeting(user, meeting):
    """
    Return True when the user can edit or cancel the meeting.

    Rules:
    - Superusers can manage all meetings.
    - The creator can manage their own meeting.
    - The linked organizer can manage their own meeting.
    - The team leader can manage meetings for their team.
    """
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    if meeting.created_by_id == user.pk:
        return True

    person = get_person_for_user(user)
    if person is None:
        return False

    return meeting.organizer_id == person.pk or meeting.team.team_leader_id == person.pk


def get_team_people(team):
    """Return active people in a team using current active memberships."""
    return Person.objects.filter(
        team_memberships__team=team,
        team_memberships__left_at__isnull=True,
        is_active=True,
    ).distinct().order_by('first_name', 'last_name')


def find_meeting_conflicts(team, start_datetime, end_datetime, ignore_meeting=None):
    """
    Find existing scheduled meetings that overlap with a proposed meeting.

    Two meetings overlap if one starts before the other ends and ends after the
    other starts. Cancelled meetings are ignored because they no longer block
    the team's calendar.
    """
    conflicts = Meeting.objects.filter(
        team=team,
        status=Meeting.Status.SCHEDULED,
        start_datetime__lt=end_datetime,
        end_datetime__gt=start_datetime,
    ).select_related('team', 'organizer')

    if ignore_meeting is not None and ignore_meeting.pk:
        conflicts = conflicts.exclude(pk=ignore_meeting.pk)

    return conflicts.order_by('start_datetime')


def build_calendar_days(year, month, meetings):
    """
    Build a month grid for the calendar template.

    Each day dictionary contains the date, whether it belongs to the selected
    month, whether it is today, and its meetings.
    """
    from calendar import Calendar

    today = timezone.localdate()
    meeting_map = {}

    for meeting in meetings:
        local_start = timezone.localtime(meeting.start_datetime)
        meeting_map.setdefault(local_start.date(), []).append(meeting)

    calendar = Calendar(firstweekday=0)
    weeks = []

    for week in calendar.monthdatescalendar(year, month):
        week_days = []
        for day in week:
            week_days.append({
                'date': day,
                'in_month': day.month == month,
                'is_today': day == today,
                'meetings': meeting_map.get(day, []),
            })
        weeks.append(week_days)

    return weeks


def get_month_bounds(year, month):
    """Return timezone-aware start/end bounds for a calendar month."""
    from datetime import datetime

    start = timezone.make_aware(datetime(year, month, 1, 0, 0, 0))
    if month == 12:
        end = timezone.make_aware(datetime(year + 1, 1, 1, 0, 0, 0))
    else:
        end = timezone.make_aware(datetime(year, month + 1, 1, 0, 0, 0))
    return start, end


def get_previous_next_month(year, month):
    """Return previous and next month/year values for calendar navigation."""
    current = date(year, month, 1)
    previous_day = current - timedelta(days=1)
    if month == 12:
        next_month = current.replace(year=year + 1, month=1)
    else:
        next_month = current.replace(month=month + 1)
    return previous_day.year, previous_day.month, next_month.year, next_month.month
