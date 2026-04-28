from django.urls import path

from . import views

app_name = 'schedules'

urlpatterns = [
    path('', views.meeting_calendar, name='meeting_calendar'),
    path('create/', views.meeting_create, name='meeting_create'),
    path('<int:pk>/', views.meeting_detail, name='meeting_detail'),
    path('<int:pk>/edit/', views.meeting_update, name='meeting_update'),
    path('<int:pk>/cancel/', views.meeting_cancel, name='meeting_cancel'),
    path('<int:pk>/respond/', views.respond_to_meeting, name='respond_to_meeting'),
]
