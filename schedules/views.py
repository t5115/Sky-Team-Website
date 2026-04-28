from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from departments.models import Department
from teams.models import Team

from .forms import MeetingForm
from .models import Meeting, MeetingParticipant
from .services import (
    build_calendar_days,
    get_month_bounds,
    get_person_for_user,
    get_previous_next_month,
    get_schedulable_teams_for_user,
    user_can_manage_meeting,
)


@login_required
def meeting_calendar(request):
    """Show meetings in a monthly calendar with filters."""
    today = timezone.localdate()

    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except ValueError:
        year = today.year
        month = today.month

    if month < 1 or month > 12:
        year = today.year
        month = today.month

    start_bound, end_bound = get_month_bounds(year, month)
    team_id = request.GET.get('team', '').strip()
    department_id = request.GET.get('department', '').strip()
    status_filter = request.GET.get('status', 'scheduled').strip()
    search_query = request.GET.get('search', '').strip()

    meetings = (
        Meeting.objects
        .filter(start_datetime__gte=start_bound, start_datetime__lt=end_bound)
        .select_related('team', 'team__department', 'organizer', 'created_by')
        .prefetch_related('participant_links__person')
    )

    if status_filter == 'scheduled':
        meetings = meetings.filter(status=Meeting.Status.SCHEDULED)
    elif status_filter == 'cancelled':
        meetings = meetings.filter(status=Meeting.Status.CANCELLED)
    elif status_filter == 'completed':
        meetings = meetings.filter(status=Meeting.Status.COMPLETED)

    if team_id:
        meetings = meetings.filter(team_id=team_id)

    if department_id:
        meetings = meetings.filter(team__department_id=department_id)

    if search_query:
        meetings = meetings.filter(
            Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(team__name__icontains=search_query)
            | Q(organizer__first_name__icontains=search_query)
            | Q(organizer__last_name__icontains=search_query)
        ).distinct()

    calendar_weeks = build_calendar_days(year, month, meetings)
    previous_year, previous_month, next_year, next_month = get_previous_next_month(year, month)

    context = {
        'calendar_weeks': calendar_weeks,
        'meetings': meetings.order_by('start_datetime'),
        'current_month_date': date(year, month, 1),
        'previous_year': previous_year,
        'previous_month': previous_month,
        'next_year': next_year,
        'next_month': next_month,
        'team_id': team_id,
        'department_id': department_id,
        'status_filter': status_filter,
        'search_query': search_query,
        'teams': Team.objects.select_related('department').order_by('name'),
        'departments': Department.objects.order_by('name'),
        'can_schedule': get_schedulable_teams_for_user(request.user).exists(),
    }
    return render(request, 'schedules/meeting_calendar.html', context)


@login_required
def meeting_detail(request, pk):
    """Show one meeting with participants and audit information."""
    meeting = get_object_or_404(
        Meeting.objects.select_related('team', 'team__department', 'organizer', 'created_by')
        .prefetch_related('participant_links__person'),
        pk=pk,
    )

    context = {
        'meeting': meeting,
        'participants': meeting.participant_links.select_related('person'),
        'can_manage': user_can_manage_meeting(request.user, meeting),
    }
    return render(request, 'schedules/meeting_detail.html', context)


@login_required
def meeting_create(request):
    """Create a new team meeting."""
    organizer = get_person_for_user(request.user)

    if not request.user.is_superuser and organizer is None:
        messages.error(request, 'Your user account is not linked to a Person profile yet. Please contact an administrator before scheduling meetings.')
        return redirect('schedules:meeting_calendar')

    if not get_schedulable_teams_for_user(request.user).exists():
        messages.error(request, 'You are not currently linked to any active team that you can schedule meetings for.')
        return redirect('schedules:meeting_calendar')

    if request.method == 'POST':
        form = MeetingForm(request.POST, user=request.user)
        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.created_by = request.user
            meeting.organizer = organizer
            meeting.save()
            form.save_participants(meeting)
            messages.success(request, 'Meeting scheduled successfully.')
            return redirect('schedules:meeting_detail', pk=meeting.pk)
    else:
        form = MeetingForm(user=request.user)

    context = {
        'form': form,
        'form_mode': 'Schedule',
    }
    return render(request, 'schedules/meeting_form.html', context)


@login_required
def meeting_update(request, pk):
    """Update an existing meeting."""
    meeting = get_object_or_404(Meeting.objects.select_related('team', 'organizer', 'created_by'), pk=pk)

    if not user_can_manage_meeting(request.user, meeting):
        messages.error(request, 'You do not have permission to edit this meeting.')
        return redirect('schedules:meeting_detail', pk=meeting.pk)

    if meeting.status == Meeting.Status.CANCELLED:
        messages.error(request, 'Cancelled meetings cannot be edited.')
        return redirect('schedules:meeting_detail', pk=meeting.pk)

    if request.method == 'POST':
        form = MeetingForm(request.POST, instance=meeting, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Meeting updated successfully.')
            return redirect('schedules:meeting_detail', pk=meeting.pk)
    else:
        form = MeetingForm(instance=meeting, user=request.user)

    context = {
        'form': form,
        'meeting': meeting,
        'form_mode': 'Edit',
    }
    return render(request, 'schedules/meeting_form.html', context)


@require_POST
@login_required
def meeting_cancel(request, pk):
    """Cancel a meeting without deleting it from the database."""
    meeting = get_object_or_404(Meeting.objects.select_related('team', 'organizer', 'created_by'), pk=pk)

    if not user_can_manage_meeting(request.user, meeting):
        messages.error(request, 'You do not have permission to cancel this meeting.')
        return redirect('schedules:meeting_detail', pk=meeting.pk)

    meeting.status = Meeting.Status.CANCELLED
    meeting.save(update_fields=['status', 'updated_at'])
    messages.success(request, 'Meeting cancelled successfully. The record was kept for history.')
    return redirect('schedules:meeting_detail', pk=meeting.pk)


@require_POST
@login_required
def respond_to_meeting(request, pk):
    """Allow an invited participant to accept, decline, or mark tentative."""
    meeting = get_object_or_404(Meeting, pk=pk)
    person = get_person_for_user(request.user)

    if person is None:
        messages.error(request, 'Your user account is not linked to a Person profile.')
        return redirect('schedules:meeting_detail', pk=meeting.pk)

    participation = get_object_or_404(MeetingParticipant, meeting=meeting, person=person)
    response_status = request.POST.get('response_status')

    allowed_statuses = {
        MeetingParticipant.ResponseStatus.ACCEPTED,
        MeetingParticipant.ResponseStatus.DECLINED,
        MeetingParticipant.ResponseStatus.TENTATIVE,
    }

    if response_status not in allowed_statuses:
        messages.error(request, 'Invalid response selected.')
        return redirect('schedules:meeting_detail', pk=meeting.pk)

    participation.response_status = response_status
    participation.responded_at = timezone.now()
    participation.save(update_fields=['response_status', 'responded_at'])
    messages.success(request, 'Your meeting response was saved.')
    return redirect('schedules:meeting_detail', pk=meeting.pk)
