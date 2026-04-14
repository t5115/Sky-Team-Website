from django.urls import path
from . import views

urlpatterns = [
    path('profile/<int:profile_id>/', views.profile_view, name='profile_view'),
    path('profile/<int:profile_id>/edit/', views.profile_edit, name='profile_edit'),
]