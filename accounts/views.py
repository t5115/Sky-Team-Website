from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from .forms import RegistrationEmailRequestForm, CompleteRegistrationForm

from django.contrib.auth.views import LoginView
from .forms import CustomAuthenticationForm

class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = CustomAuthenticationForm

def request_registration_link_view(request):
    """
    Step 1:
    Ask the user for an email address and, if appropriate,
    send a time-limited registration link.
    """
    if request.method == "POST":
        form = RegistrationEmailRequestForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"]

            # Check whether the email already belongs to an existing user.
            user_exists = User.objects.filter(email__iexact=email).exists()

            # Secure UX choice:
            # We return the same response either way.
            # If the email is not registered, we send the registration link.
            if not user_exists:
                signer = TimestampSigner()
                signed_email = signer.sign(email)

                registration_path = reverse(
                "complete_registration",
                 kwargs={"signed_email": signed_email}
                 )
                registration_link = request.build_absolute_uri(registration_path)

                print( registration_link )
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
            else : 
                return render(request, "accounts/registration_email_already_used.html")

            return render(request, "accounts/registration_link_sent.html")
    else:
        form = RegistrationEmailRequestForm()

    return render(
        request,
        "accounts/request_registration_link.html",
        {"form": form}
    )


def complete_registration_view(request, signed_email):
    """
    Step 2:
    Verify the signed email link and allow the user to set a password.
    """
    signer = TimestampSigner()

    try:
        email = signer.unsign(
            signed_email,
            max_age=settings.REGISTRATION_LINK_MAX_AGE
        )
    except (BadSignature, SignatureExpired):
        return render(request, "accounts/registration_link_invalid.html")

    # Extra safety check in case the email became registered after the link was sent.
    if User.objects.filter(email__iexact=email).exists():
        return render(request, "accounts/registration_email_already_used.html", {"email": email})

    if request.method == "POST":
        form = CompleteRegistrationForm(request.POST)

        if form.is_valid():
            password = form.cleaned_data["password1"]

            user = User.objects.create_user(
                username=email,   # Because default Django auth uses username
                email=email,
                password=password
            )

            return render(request, "accounts/registration_success.html", {"email": email})
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
