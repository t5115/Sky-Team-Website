from django.urls import path

from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.organization_report, name='organization_report'),
    path('download/', views.download_organization_report_csv, name='download_organization_report_csv'),
]
