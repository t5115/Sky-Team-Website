from django.contrib import admin

from .models import TeamResource


@admin.register(TeamResource)
class TeamResourceAdmin(admin.ModelAdmin):
    """Admin configuration for team-owned resources."""

    list_display = ('name', 'resource_type', 'team', 'is_active', 'updated_at')
    list_filter = ('resource_type', 'is_active', 'team__department')
    search_fields = ('name', 'description', 'team__name', 'contact_detail', 'url')
    autocomplete_fields = ('team',)
    readonly_fields = ('created_at', 'updated_at')
