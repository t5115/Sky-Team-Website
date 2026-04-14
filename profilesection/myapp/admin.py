from django.contrib import admin
from .models import Profile
# Register your models here.
admin.site.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", 'name', 'email', 'department', 'role', 'team', 'phone_number')
    search_fields = ('name', 'email', 'department', 'role', 'team')