# Import Django's generic views for displaying and editing objects
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView

# Import authentication mixins
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# Import Q so we can build OR-based search conditions across multiple fields
from django.db.models import Q

# Import reverse_lazy to build success URLs cleanly
from django.urls import reverse_lazy

# Import the Person model so the views can read Person records from the database
from .models import Person
# Import the form used for editing Person profiles 
from .forms import PersonForm , PersonCreateForm

# Import helper to fetch an object or raise 404 if it does not exist
from django.shortcuts import get_object_or_404, redirect

# Import decorators for authentication and POST-only access
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

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
    

class PersonDetailView(LoginRequiredMixin, DetailView):
    """
    Display one person's profile page.

    Any logged-in user can view a person's profile.
    The template will decide whether Edit and Deactivate buttons
    should be shown based on the current user's permissions.
    """

    # The model this detail view works with
    model = Person

    # The HTML template used to render the person profile page
    template_name = "people/person_detail.html"

    # The name used in the template for the Person object
    context_object_name = "person"

    def get_context_data(self, **kwargs):
        """
        Add extra context flags used by the template
        to decide whether Edit/Deactivate buttons should appear.
        """
        # Get the default context from DetailView
        context = super().get_context_data(**kwargs)

        # The profile currently being viewed
        person = self.get_object()

        # The currently logged-in user
        current_user = self.request.user

        # Superusers can manage every profile
        is_superuser = current_user.is_superuser

        # A regular user can manage only their own linked Person profile
        is_own_profile = person.user == current_user

        # A profile is manageable if:
        # - the current user is a superuser
        # OR
        # - the current user is viewing their own profile
        context["can_manage_profile"] = is_superuser or is_own_profile

        # Add smaller flags too because they make the template easier to read
        context["is_own_profile"] = is_own_profile
        context["is_superuser_viewer"] = is_superuser

        return context
class PersonCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Create a new Person profile.

    Only superusers are allowed to access this page.

    This view uses a dedicated create form because the create workflow
    supports optional linking to an existing User account, while the
    normal edit form does not expose that field.
    """

    # The model this create view works with
    model = Person

    # Use the dedicated create form
    form_class = PersonCreateForm

    # Reuse the same Bootstrap form template used by the edit page
    template_name = "people/person_form.html"

    # Return HTTP 403 for logged-in users who are not allowed
    raise_exception = True

    def test_func(self):
        """
        Allow access only to superusers.
        """
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        """
        Add extra template context so the shared form template
        can display the correct title, subtitle, and cancel link.
        """
        context = super().get_context_data(**kwargs)

        context["form_mode"] = "create"
        context["page_title"] = "Add New Profile"
        context["page_subtitle"] = "Create a new person profile and optionally link it to an existing user account."

        return context

    def get_success_url(self):
        """
        After successful creation, redirect to the new person's detail page.
        """
        return reverse_lazy("people:person_detail", kwargs={"pk": self.object.pk})


class PersonUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Update an existing Person profile.

    Permission rules:
    - superusers can edit any profile
    - regular users can edit only their own linked Person profile
    """

    # The model this update view edits
    model = Person

    # The form used to update the person
    form_class = PersonForm
    
    

    
    # The HTML template used to render the edit form
    template_name = "people/person_form.html"

    def test_func(self):
        """
        Return True only if the current user is allowed to edit this profile.
        """
        # The person record being edited
        person = self.get_object()

        # The currently logged-in user
        current_user = self.request.user

        # Superusers can edit any profile
        if current_user.is_superuser:
            return True

        # Regular users can edit only their own linked profile
        return person.user == current_user

    def get_success_url(self):
        """
        Redirect back to the person's detail page after a successful update.
        """
        return reverse_lazy("people:person_detail", kwargs={"pk": self.object.pk})
    def get_context_data(self, **kwargs):
        """
        Add extra context so the shared form template can show
        edit-specific titles and links.
        """
        context = super().get_context_data(**kwargs)

        context["form_mode"] = "edit"
        context["page_title"] = "Edit Profile"
        context["page_subtitle"] = (
            f"Update profile information for {self.object.first_name} {self.object.last_name}"
        )

        return context
@login_required
@require_POST
def deactivate_person_view(request, pk):
    """
    Deactivate a Person profile by setting is_active to False.

    Permission rules:
    - superusers can deactivate any profile
    - regular users can deactivate only their own linked profile
    """

    # Find the Person record or return 404 if it does not exist
    person = get_object_or_404(Person, pk=pk)

    # The currently logged-in user
    current_user = request.user

    # Check whether this user is allowed to deactivate this profile
    can_deactivate = current_user.is_superuser or person.user == current_user

    # If the user is not allowed, redirect them back to the profile page
    if not can_deactivate:
        return redirect("people:person_detail", pk=person.pk)

    # Perform a soft delete by marking the profile as inactive
    person.is_active = False

    # Save only the changed field for efficiency and clarity
    person.save(update_fields=["is_active"])

    # Redirect after success
    # If a regular user deactivates their own profile, sending them to the list page is reasonable.
    # If a superuser deactivates someone else's profile, the detail page is also acceptable.
    return redirect("people:person_detail", pk=person.pk)



@login_required
@require_POST
def reactivate_person_view(request, pk):
    """
    Reactivate a Person profile by setting is_active to True.

    Permission rules:
    - superusers can reactivate any profile
    - regular users can reactivate only their own linked profile
    """

    # Find the Person record or return 404 if it does not exist
    person = get_object_or_404(Person, pk=pk)

    # The currently logged-in user
    current_user = request.user

    # Check whether this user is allowed to reactivate this profile
    can_reactivate = current_user.is_superuser or person.user == current_user

    # If the user is not allowed, redirect them back to the profile page
    if not can_reactivate:
        return redirect("people:person_detail", pk=person.pk)

    # Reactivate the profile
    person.is_active = True

    # Save only the changed field
    person.save(update_fields=["is_active"])

    # Redirect back to the profile page
    return redirect("people:person_detail", pk=person.pk)