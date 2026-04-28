from django.urls import path

from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('new/', views.conversation_start, name='conversation_start'),
    path('<int:pk>/', views.conversation_detail, name='conversation_detail'),
    path('<int:pk>/archive/', views.archive, name='archive'),
    path('<int:pk>/unarchive/', views.unarchive, name='unarchive'),
    path('<int:pk>/leave/', views.leave, name='leave'),
    path('messages/<int:pk>/delete/', views.delete_message, name='delete_message'),
]
