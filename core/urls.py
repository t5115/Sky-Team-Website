from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('organisation-diagram/', views.organisation_diagram, name='organisation_diagram'),
]
