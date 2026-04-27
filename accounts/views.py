from django.conf import settings
from django.contrib.auth.models import User
from django.core import signing
from django.core.mail import EmailMessage
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from urllib.parse import urlencode

from django.contrib.auth.views import LoginView
from .forms import (
    RegistrationEmailRequestForm,
    CompleteRegistrationForm,
    CustomAuthenticationForm,
)


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = CustomAuthenticationForm


def request_registration_link_view(request):
    if request.method == "POST":
        form = RegistrationEmailRequestForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"]
            user_exists = User.objects.filter(email__iexact=email).exists()

            if not user_exists:
                token = signing.dumps(email)

                registration_path = reverse("complete_registration")
                query_string = urlencode({"token": token})
                registration_link = request.build_absolute_uri(
                    f"{registration_path}?{query_string}"
                )

                print(registration_link)

                subject = "Complete your Sky project registration"
                message = render_to_string(
                    "accounts/registration_link_email.txt",
                    {
                        "registration_link": registration_link,
                        "email": email,
                    }
                )

                email_message = EmailMessage(
                    subject=subject,
                    body=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[email],
                )
                email_message.send()

            return render(request, "accounts/registration_link_sent.html")
    else:
        form = RegistrationEmailRequestForm()

    return render(
        request,
        "accounts/request_registration_link.html",
        {"form": form}
    )


def complete_registration_view(request):
    token = request.GET.get("token")

    if not token:
        return render(request, "accounts/registration_link_invalid.html")

    try:
        email = signing.loads(
            token,
            max_age=settings.REGISTRATION_LINK_MAX_AGE
        )
    except signing.BadSignature:
        return render(request, "accounts/registration_link_invalid.html")
    except signing.SignatureExpired:
        return render(request, "accounts/registration_link_invalid.html")

    if User.objects.filter(email__iexact=email).exists():
        return render(
            request,
            "accounts/registration_email_already_used.html",
            {"email": email}
        )

    if request.method == "POST":
        form = CompleteRegistrationForm(request.POST)

        if form.is_valid():
            password = form.cleaned_data["password1"]

            User.objects.create_user(
                username=email,
                email=email,
                password=password
            )

            return render(
                request,
                "accounts/registration_success.html",
                {"email": email}
            )
    else:
        form = CompleteRegistrationForm()

    return render(
        request,
        "accounts/complete_registration.html",
        {
            "form": form,
            "email": email,
        }
    )