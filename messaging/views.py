from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from people.models import Person
from .forms import MessageForm
from .models import Message


@login_required
def message_list_view(request, user_id=None):
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

        messages = Message.objects.filter(
            Q(sender=request.user, recipient=selected_user) |
            Q(sender=selected_user, recipient=request.user)
        ).order_by("timestamp")

        Message.objects.filter(
            sender=selected_user,
            recipient=request.user,
            is_read=False
        ).update(is_read=True)

        form = MessageForm()

    context = {
        "people": people,
        "selected_user": selected_user,
        "messages": messages,
        "form": form,
    }
    return render(request, "messages.html", context)


@login_required
def send_message_view(request, user_id):
    recipient = get_object_or_404(User, pk=user_id)

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.recipient = recipient
            message.save()

    return redirect("messaging:conversation", user_id=user_id)