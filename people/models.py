

# Import the active user model safely through settings, which is the Django best practice.
from django.conf import settings

# Import ValidationError so we can raise meaningful model validation errors.
from django.core.exceptions import ValidationError

# Import Django's model classes to define the database table structure.
from django.db import models




class Person(models.Model):
    """
    Represents a person inside the organization structure.

    Important business rules:
    - A Person may exist without a linked User account.
    - A User may exist without a linked Person record.
    - If a Person is linked to a User, both emails must match.
    - Person.email must belong to an allowed company domain from settings.
    """

    # Optional one-to-one link to the authentication user.
    # We use SET_NULL because if the user account is deleted, we may still want
    # to keep the Person record for organizational history or audit reasons.
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="person_profile",
    )

    # Required personal identity fields.
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    # Optional organizational fields.
    role = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=150, blank=True)

    # Required and unique email.
    # This is a core identity/contact field for the person.
    email = models.EmailField(unique=True)

    # Optional contact field.
    phone_number = models.CharField(max_length=30, blank=True)

    # Temporary text fields for team and department.
    # Later these can be replaced with ForeignKey fields.
    team_name = models.CharField(max_length=120, blank=True)
    department_name = models.CharField(max_length=120, blank=True)

    # Soft-delete / deactivation behavior.
    is_active = models.BooleanField(default=True)

    # Automatic timestamps for auditing and system behavior.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Default ordering when people are listed.
        ordering = ["first_name", "last_name"]

    def __str__(self):
        """
        Human-readable representation of the object.
        """
        return f"{self.first_name} {self.last_name}"

    def clean(self):
        """
        Central place for business validation rules.

        Django calls this during model validation (for example through ModelForms).
        We also call full_clean() inside save() so these rules are enforced
        whenever the model is saved in application code.
        """
        super().clean()

        errors = {}

       
        # Normalize string values first
      

        # Strip surrounding spaces from text fields if values exist.
        if self.first_name is not None:
            self.first_name = self.first_name.strip()

        if self.last_name is not None:
            self.last_name = self.last_name.strip()

        if self.role is not None:
            self.role = self.role.strip()

        if self.job_title is not None:
            self.job_title = self.job_title.strip()

        if self.email is not None:
            self.email = self.email.strip().lower()

        if self.phone_number is not None:
            self.phone_number = self.phone_number.strip()

        if self.team_name is not None:
            self.team_name = self.team_name.strip()

        if self.department_name is not None:
            self.department_name = self.department_name.strip()

        
        # Required fields must not be only whitespace
       

        if not self.first_name:
            errors["first_name"] = "First name is required and cannot be blank."

        if not self.last_name:
            errors["last_name"] = "Last name is required and cannot be blank."

        if not self.email:
            errors["email"] = "Email is required and cannot be blank."

      
        # Email domain must be from the allowed company domains setting
       

        # Only continue if email exists and looks splittable.
        if self.email and "@" in self.email:
            email_domain = self.email.split("@")[-1].lower()

            # Read allowed domains from Django settings.
            # If the setting is missing, default to an empty list.
            allowed_domains = getattr(settings, "ALLOWED_EMAIL_DOMAINS", [])


            if allowed_domains and email_domain not in allowed_domains:
                errors["email"] = (
                    f"Email domain '{email_domain}' is not allowed. "
                    f"Allowed domains: {allowed_domains}."
                )

      
        # If a linked user exists, both emails must be equal
        

        if self.user:
            # Normalize user email too before comparison.
            user_email = (self.user.email or "").strip().lower()

            if not user_email:
                errors["user"] = "The linked user must have an email address."

            elif self.email and self.email != user_email:
                errors["email"] = "The person's email must match the linked user's email."

        
        
       

      

        
        # Raise all collected validation errors
        

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """
        Enforce validation every time the model is saved.

        This is important because Django does NOT automatically call full_clean()
        on save(). By calling it here, we make sure business rules are enforced
        not only in forms/admin, but also in normal Python code.
        """
        self.full_clean()
        super().save(*args, **kwargs)
