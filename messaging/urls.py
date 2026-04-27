from django.urls import path
from . import views

app_name = "messaging"

urlpatterns = [
    path("", views.message_list_view, name="message_list"),
    path("<int:user_id>/", views.message_list_view, name="conversation"),
    path("<int:user_id>/send/", views.send_message_view, name="send_message"),
]