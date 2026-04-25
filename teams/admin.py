from django.contrib import admin
from .models import Team, TeamMembership


class TeamMembershipInline(admin.TabularInline):
    model = TeamMembership
    extra = 1
    autocomplete_fields = ['person']
    fields = ('person', 'role', 'is_primary_contact', 'joined_at', 'left_at')
    readonly_fields = ('joined_at',)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'department_name', 'status', 'member_count', 'team_leader')
    list_filter = ('status', 'department_name')
    search_fields = ('name', 'department_name')
    autocomplete_fields = ['team_leader']
    inlines = [TeamMembershipInline]


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ('team', 'person', 'role', 'is_primary_contact', 'joined_at', 'left_at')
    list_filter = ('team', 'is_primary_contact')
    search_fields = ('person__first_name', 'person__last_name', 'team__name')
    autocomplete_fields = ['team', 'person']
