from django.contrib import admin
from .models import Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'department_head', 'team_count', 'created_at')
    search_fields = ('name', 'description')
    autocomplete_fields = ['department_head']

