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

    # Route for viewing one person's profile 
    path("<int:pk>/" , views.PersonDetailView.as_view() , name = "person_detail" ) , 

   # Route for adding a new profile
    path("add/", views.PersonCreateView.as_view(), name="person_create") , 
    
    # Route for editing one person's profile 
    path("<int:pk>/edit/" , views.PersonUpdateView.as_view() , name= "person_edit") , 

    # Route for deactivating one person's profile
    path("<int:pk>/deactivate/", views.deactivate_person_view, name="person_deactivate"),

    # Route for reactivating one person's profile
    path("<int:pk>/reactivate/", views.reactivate_person_view, name="person_reactivate"),

]
