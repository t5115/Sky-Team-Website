# Import Django's forms framework
from django import forms

# Import the Person model
from .models import Person


class PersonForm(forms.ModelForm):
    """
    Form used for editing and creating a Person profile.
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