from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from people.models import Person
from .forms import MessageForm
from .models import Message


@login_required
def message_list_view(request, user_id=None):
    folder = request.GET.get("folder", "inbox")

    # Only show OTHER active people who have linked user accounts
    people = (
        Person.objects
        .filter(user__isnull=False, is_active=True)
        .exclude(user=request.user)
        .order_by("first_name", "last_name")
    )

    selected_user = None
    messages = Message.objects.none()
    form = None

    if user_id is not None:
        selected_user = get_object_or_404(User, pk=user_id)

        # Prevent messaging yourself
        if selected_user == request.user:
            return redirect(f"{reverse('messaging:message_list')}?folder={folder}")

        if folder == "inbox":
            messages = Message.objects.filter(
                sender=selected_user,
                recipient=request.user,
                is_draft=False,
            ).order_by("timestamp")

            Message.objects.filter(
                sender=selected_user,
                recipient=request.user,
                is_read=False,
                is_draft=False,
            ).update(is_read=True)

        elif folder == "sent":
            messages = Message.objects.filter(
                sender=request.user,
                recipient=selected_user,
                is_draft=False,
            ).order_by("timestamp")

        elif folder == "drafts":
            messages = Message.objects.filter(
                sender=request.user,
                recipient=selected_user,
                is_draft=True,
            ).order_by("timestamp")

        form = MessageForm()

    context = {
        "people": people,
        "selected_user": selected_user,
        "messages": messages,
        "form": form,
        "folder": folder,
    }
    return render(request, "messages.html", context)


@login_required
def send_message_view(request, user_id):
    recipient = get_object_or_404(User, pk=user_id)

    # Prevent sending messages to yourself
    if recipient == request.user:
        return redirect("messaging:message_list")

    if request.method == "POST":
        form = MessageForm(request.POST)
        action = request.POST.get("action", "send")

        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.recipient = recipient

            if action == "draft":
                message.is_draft = True
                message.save()
                query = urlencode({"folder": "drafts"})
            else:
                message.is_draft = False
                message.save()
                query = urlencode({"folder": "sent"})

            url = reverse("messaging:conversation", kwargs={"user_id": user_id})
            return redirect(f"{url}?{query}")

    url = reverse("messaging:conversation", kwargs={"user_id": user_id})
    return redirect(f"{url}?folder=inbox")