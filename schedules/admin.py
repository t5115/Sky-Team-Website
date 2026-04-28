from django.contrib import admin

from .models import Meeting, MeetingParticipant


class MeetingParticipantInline(admin.TabularInline):
    model = MeetingParticipant
    extra = 0


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ['title', 'team', 'start_datetime', 'end_datetime', 'status', 'organizer']
    list_filter = ['status', 'visibility', 'team']
    search_fields = ['title', 'description', 'team__name', 'organizer__first_name', 'organizer__last_name']
    inlines = [MeetingParticipantInline]


@admin.register(MeetingParticipant)
class MeetingParticipantAdmin(admin.ModelAdmin):
    list_display = ['meeting', 'person', 'response_status', 'invited_at', 'responded_at']
    list_filter = ['response_status']
    search_fields = ['meeting__title', 'person__first_name', 'person__last_name', 'person__email']
