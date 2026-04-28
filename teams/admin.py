from django.contrib import admin

from .models import Team, TeamDependency, TeamMembership


class TeamMembershipInline(admin.TabularInline):
    model = TeamMembership
    extra = 1
    autocomplete_fields = ['person']
    fields = ('person', 'role', 'is_primary_contact', 'joined_at', 'left_at')
    readonly_fields = ('joined_at',)


class TeamDependencyInline(admin.TabularInline):
    """
    Allow admins to manage dependencies directly from the Team admin page.

    fk_name is required because TeamDependency has two foreign keys to Team.
    It tells Django that this inline is editing dependencies where the current
    Team is the dependent_team.
    """
    model = TeamDependency
    fk_name = 'dependent_team'
    extra = 1
    autocomplete_fields = ['required_team']
    fields = ('required_team', 'reason', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'department_name',
        'status',
        'member_count',
        'dependency_count',
        'dependent_team_count',
        'team_leader',
    )
    list_filter = ('status', 'department_name', 'department')
    search_fields = ('name', 'department_name', 'department__name')
    autocomplete_fields = ['team_leader', 'department']
    inlines = [TeamMembershipInline, TeamDependencyInline]


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ('team', 'person', 'role', 'is_primary_contact', 'joined_at', 'left_at')
    list_filter = ('team', 'is_primary_contact')
    search_fields = ('person__first_name', 'person__last_name', 'team__name')
    autocomplete_fields = ['team', 'person']


@admin.register(TeamDependency)
class TeamDependencyAdmin(admin.ModelAdmin):
    list_display = ('dependent_team', 'required_team', 'created_at', 'updated_at')
    list_filter = ('dependent_team', 'required_team')
    search_fields = ('dependent_team__name', 'required_team__name', 'reason')
    autocomplete_fields = ['dependent_team', 'required_team']
    readonly_fields = ('created_at', 'updated_at')
