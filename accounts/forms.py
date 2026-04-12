from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control form-control-lg",
            "placeholder": "Enter your username"
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control form-control-lg",
            "placeholder": "Enter your password"
        })
    )

class RegistrationEmailRequestForm(forms.Form):
    """
    First step of the registration flow.

    The user enters an email address.
    We validate:
    - correct email format
    - optional allowed domain restriction
    """
    email = forms.EmailField(
        max_length=320,
        label="Email address",
        help_text="Enter your work email address."
    )

    def clean_email(self):
        """
        Normalize and validate the email.
        """
        email = self.cleaned_data["email"].strip().lower()

        allowed_domains = getattr(settings, "ALLOWED_EMAIL_DOMAINS", [])

        # If the list is empty, all domains are allowed during development/testing.
        if allowed_domains:
            domain = email.split("@", 1)[1]
            if domain not in allowed_domains:
                raise ValidationError("Please use an approved company email address.")

        return email


class CompleteRegistrationForm(forms.Form):
    """
    Second step of the registration flow.

    The email has already been verified through the emailed link,
    so we only ask the user to choose a password.
    """
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        help_text="Choose a strong password."
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput
    )

    def clean(self):
        """
        Cross-field validation:
        password1 and password2 must match.
        """
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError("The two password fields must match.")

        return cleaned_data