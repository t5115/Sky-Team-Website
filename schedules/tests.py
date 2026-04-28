from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from departments.models import Department
from people.models import Person
from teams.models import Team, TeamMembership

from .models import Meeting
from .services import find_meeting_conflicts, get_schedulable_teams_for_user


class ScheduleFeatureTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='member', email='member@sky.com', password='pass')
        self.person = Person.objects.create(
            user=self.user,
            first_name='Team',
            last_name='Member',
            email='member@sky.com',
        )
        self.department = Department.objects.create(name='Engineering')
        self.team = Team.objects.create(name='Platform Team', department=self.department)
        TeamMembership.objects.create(team=self.team, person=self.person)

    def test_member_can_schedule_for_own_team(self):
        teams = get_schedulable_teams_for_user(self.user)
        self.assertIn(self.team, teams)

    def test_meeting_end_must_be_after_start(self):
        start = timezone.now() + timedelta(days=1)
        meeting = Meeting(
            team=self.team,
            created_by=self.user,
            organizer=self.person,
            title='Invalid meeting',
            start_datetime=start,
            end_datetime=start,
        )
        with self.assertRaises(ValidationError):
            meeting.full_clean()

    def test_overlapping_team_meeting_is_detected(self):
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=1)
        Meeting.objects.create(
            team=self.team,
            created_by=self.user,
            organizer=self.person,
            title='Existing meeting',
            start_datetime=start,
            end_datetime=end,
        )
        conflicts = find_meeting_conflicts(
            team=self.team,
            start_datetime=start + timedelta(minutes=30),
            end_datetime=end + timedelta(minutes=30),
        )
        self.assertTrue(conflicts.exists())
