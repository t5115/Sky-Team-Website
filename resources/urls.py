from django.urls import path

from . import views

app_name = 'resources'

urlpatterns = [
    # Sidebar pages. Each page shows one resource type only.
    path('services/', views.service_list, name='service_list'),
    path('repositories/', views.repository_list, name='repository_list'),
    path('contact-channels/', views.contact_channel_list, name='contact_channel_list'),

    # Shared create/edit/status actions for all three resource types.
    path('<str:resource_type>/add/', views.resource_create, name='resource_create'),
    path('<int:pk>/edit/', views.resource_update, name='resource_update'),
    path('<int:pk>/deactivate/', views.resource_deactivate, name='resource_deactivate'),
    path('<int:pk>/reactivate/', views.resource_reactivate, name='resource_reactivate'),
]
