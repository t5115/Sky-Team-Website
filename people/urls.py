# Import the path function used to define URL patterns
from django.urls import path

# Import views from the current app
from . import views

# Namespace for this app's URLs
app_name = "people"

# List of URL patterns for the People app
urlpatterns = [
    # Route for the People list page
    path("", views.PersonListView.as_view(), name="person_list"),
]
