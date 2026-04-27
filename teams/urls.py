from django.urls import path

from . import views

app_name = 'teams'

urlpatterns = [
    path('', views.team_list, name='team_list'),
    path('dependencies/', views.team_dependency_overview, name='team_dependency_overview'),
    path('<int:pk>/dependencies/', views.manage_team_dependencies, name='manage_team_dependencies'),
    path(
        '<int:pk>/dependencies/<int:dependency_id>/delete/',
        views.delete_team_dependency,
        name='delete_team_dependency',
    ),
]
