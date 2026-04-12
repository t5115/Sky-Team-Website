from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LoginView
from .views import request_registration_link_view, complete_registration_view

urlpatterns = [
    path(
        "login/",
        LoginView.as_view(template_name="accounts/login.html"),
        name="CustomLoginView",
    ),
    path(
        "register/",
        request_registration_link_view,
        name="request_registration_link",
    ),
    path(
    "register/complete/<path:signed_email>/",
    complete_registration_view,
    name="complete_registration",
)
]

