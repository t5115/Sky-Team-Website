# Import Django's generic ListView for pages that display multiple objects
from django.views.generic import ListView

# Import a mixin that forces the user to be logged in before accessing the page
from django.contrib.auth.mixins import LoginRequiredMixin

# Import the Person model so the view can read Person records from the database
from .models import Person


class PersonListView(LoginRequiredMixin, ListView):
    """
    Display a list of Person records.

    This is the first page of the People module and acts as the
    directory page where users can browse people in the organization.
    """

    # The model this list view works with
    model = Person

    # The HTML template that will be used to display the page
    template_name = "people/person_list.html"

    # The name used in the template to access the queryset
    context_object_name = "people"

    # Order the records alphabetically
    ordering = ["first_name", "last_name"]

    # Number of records shown per page
    paginate_by = 10
