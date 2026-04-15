# Import Django's generic ListView for pages that display multiple objects
from django.views.generic import ListView

# Import a mixin that forces the user to be logged in before accessing the page
from django.contrib.auth.mixins import LoginRequiredMixin

# Import Q so we can build OR-based search conditions across multiple fields
from django.db.models import Q

# Import the Person model so the view can read Person records from the database
from .models import Person


class PersonListView(LoginRequiredMixin, ListView):
    """
    Display a list of Person records.

    This page supports:
    - free-text search
    - department filtering
    """

    # The model this list view works with
    model = Person

    # The HTML template used to render the page
    template_name = "people/person_list.html"

    # The name the template will use for the queryset
    context_object_name = "people"

    # Number of records shown per page
    paginate_by = 10

    def get_queryset(self):
        """
        Build and return the queryset for the People list page.

        We start with all Person records, then optionally apply:
        - text search
        - department filtering
        """
        # Start with all people ordered alphabetically
        queryset = Person.objects.all().order_by("first_name", "last_name")

        # Read the search term from the URL query string
        search_query = self.request.GET.get("q", "").strip()

        # Read the selected department from the URL query string
        selected_department = self.request.GET.get("department", "").strip()

        # Apply text search if the user entered something
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(job_title__icontains=search_query)|
                Q(team_name__icontains=search_query)
            )

        # Apply department filtering if the user selected a department
        if selected_department:
            queryset = queryset.filter(department_name=selected_department)

        return queryset

    def get_context_data(self, **kwargs):
        """
        Add extra context data for the template.

        Here we send the list of available departments so the dropdown
        can be built dynamically.
        """
        # Get the default context from the parent ListView
        context = super().get_context_data(**kwargs)

        # Query all distinct non-empty department names
        departments = (
            Person.objects.exclude(department_name="")
            .values_list("department_name", flat=True)
            .distinct()
            .order_by("department_name")
        )

        # Add the departments list to the template context
        context["departments"] = departments

        return context