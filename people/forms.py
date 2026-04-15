# Import Django's forms framework
from django import forms

# Import Django's built-in User model helper safely
from django.contrib.auth import get_user_model

# Import the Person model
from .models import Person


# Get the active User model used by the project
User = get_user_model()


class PersonForm(forms.ModelForm):
    """
    Form used for editing an existing Person profile.

    This form is intentionally limited to normal profile fields.
    We do NOT expose the linked user field here because:
    - regular users should only edit their own profile information
    - linking/unlinking accounts is an admin-level action
    """

    class Meta:
        model = Person
        fields = [
            "first_name",
            "last_name",
            "role",
            "job_title",
            "email",
            "phone_number",
            "team_name",
            "department_name",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "role": forms.TextInput(attrs={"class": "form-control"}),
            "job_title": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "team_name": forms.TextInput(attrs={"class": "form-control"}),
            "department_name": forms.TextInput(attrs={"class": "form-control"}),
        }


class PersonCreateForm(forms.ModelForm):
    """
    Form used by superusers to create a new Person profile.

    This form includes an OPTIONAL linked user field.
    If a user is selected:
    - that user must not already be linked to another Person
    - the person's email must match the linked user's email

    We keep this form separate from PersonForm because only superusers
    should be able to perform account-linking during profile creation.
    """

    # Optional dropdown to link this new Person to an existing User account
    user = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        empty_label="No linked user account",
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text="Optional. Link this profile to an existing user account.",
    )

    class Meta:
        model = Person
        fields = [
            "user",
            "first_name",
            "last_name",
            "role",
            "job_title",
            "email",
            "phone_number",
            "team_name",
            "department_name",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "role": forms.TextInput(attrs={"class": "form-control"}),
            "job_title": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "team_name": forms.TextInput(attrs={"class": "form-control"}),
            "department_name": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        """
        Customize the user dropdown so it only shows users
        that are not already linked to a Person profile.

        This is important because Person.user is a OneToOneField,
        so one User can only be linked to one Person.
        """
        super().__init__(*args, **kwargs)

        # Get all users that do not already have a linked person profile
        # "person_profile" comes from related_name in the Person model
        available_users = User.objects.filter(person_profile__isnull=True).order_by("email")

        # If we are editing an existing instance in the future and it already has a linked user,
        # include that user too so the current value remains selectable.
        if self.instance and self.instance.pk and self.instance.user:
            available_users = (User.objects.filter(pk=self.instance.user.pk) | available_users).distinct()

        self.fields["user"].queryset = available_users

    def clean(self):
        """
        Add form-level validation for the optional user linking.

        Django recommends calling super().clean() first so built-in
        ModelForm validation continues to work properly.
        """
        cleaned_data = super().clean()

        selected_user = cleaned_data.get("user")
        email = cleaned_data.get("email")

        # If no user was selected, nothing more is needed here
        if not selected_user:
            return cleaned_data

        # Normalize both emails before comparing
        selected_user_email = (selected_user.email or "").strip().lower()
        person_email = (email or "").strip().lower()

        # The selected user must have an email address
        if not selected_user_email:
            self.add_error("user", "The selected user account does not have an email address.")

        # If a linked user is selected, the emails must match
        if person_email and selected_user_email and person_email != selected_user_email:
            self.add_error("email", "The person's email must match the selected user's email.")

        return cleaned_data