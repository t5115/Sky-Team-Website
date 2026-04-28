from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ConversationStartForm, MessageForm
from .models import Conversation, ConversationParticipant, Message
from .services import (
    archive_conversation,
    create_group_conversation,
    get_active_team_users,
    get_or_create_direct_conversation,
    get_user_conversations,
    leave_conversation,
    mark_conversation_read,
    send_message,
    unread_count_for_conversation,
    user_can_access_conversation,
)

User = get_user_model()


@login_required
def inbox(request):
    """Display the current user's messaging inbox."""
    search_query = request.GET.get('q', '').strip()
    show_archived = request.GET.get('archived') == '1'
    conversations = get_user_conversations(request.user, include_archived=show_archived)

    if search_query:
        conversations = conversations.filter(
            Q(title__icontains=search_query)
            | Q(team__name__icontains=search_query)
            | Q(participant_links__user__username__icontains=search_query)
            | Q(participant_links__user__email__icontains=search_query)
            | Q(messages__body__icontains=search_query)
        ).distinct()

    conversation_cards = []
    for conversation in conversations:
        last_message = conversation.messages.select_related('sender').filter(deleted_at__isnull=True).order_by('-sent_at').first()
        participant_names = conversation.participant_links.filter(left_at__isnull=True).select_related('user')[:4]
        conversation_cards.append({
            'conversation': conversation,
            'last_message': last_message,
            'participants': participant_names,
            'unread_count': unread_count_for_conversation(conversation, request.user),
        })

    return render(request, 'messaging/inbox.html', {
        'conversation_cards': conversation_cards,
        'search_query': search_query,
        'show_archived': show_archived,
    })


@login_required
def conversation_detail(request, pk):
    """Show a full message thread and allow the user to send a new message."""
    conversation = get_object_or_404(
        Conversation.objects.select_related('team', 'created_by').prefetch_related('participant_links__user'),
        pk=pk,
    )
    if not user_can_access_conversation(request.user, conversation):
        messages.error(request, 'You do not have access to this conversation.')
        return redirect('messaging:inbox')

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            try:
                send_message(
                    conversation=conversation,
                    sender=request.user,
                    body=form.cleaned_data['body'],
                    attachment_url=form.cleaned_data.get('attachment_url', ''),
                )
                messages.success(request, 'Message sent.')
                return redirect('messaging:conversation_detail', pk=conversation.pk)
            except PermissionError:
                messages.error(request, 'You are not allowed to send messages in this conversation.')
    else:
        form = MessageForm()

    mark_conversation_read(conversation, request.user)
    message_list = conversation.messages.select_related('sender').prefetch_related('read_receipts__user').order_by('sent_at')
    participant_link = ConversationParticipant.objects.get(conversation=conversation, user=request.user)

    return render(request, 'messaging/conversation_detail.html', {
        'conversation': conversation,
        'messages_list': message_list,
        'participants': conversation.participant_links.filter(left_at__isnull=True).select_related('user'),
        'form': form,
        'participant_link': participant_link,
    })


@login_required
def conversation_start(request):
    """Create a direct, group, or team conversation."""
    if request.method == 'POST':
        form = ConversationStartForm(request.POST, user=request.user)
        if form.is_valid():
            mode = form.cleaned_data['mode']
            first_message = form.cleaned_data['first_message']
            if mode == 'direct':
                conversation, created = get_or_create_direct_conversation(request.user, form.cleaned_data['recipient'])
            elif mode == 'group':
                users = list(form.cleaned_data['participants']) + [request.user]
                conversation = create_group_conversation(request.user, form.cleaned_data['title'], users)
            else:
                team = form.cleaned_data['team']
                users = list(get_active_team_users(team))
                if request.user not in users:
                    users.append(request.user)
                conversation = create_group_conversation(
                    created_by=request.user,
                    title=form.cleaned_data['title'] or f'{team.name} team chat',
                    users=users,
                    team=team,
                )
            send_message(conversation, request.user, first_message)
            messages.success(request, 'Conversation created successfully.')
            return redirect('messaging:conversation_detail', pk=conversation.pk)
    else:
        form = ConversationStartForm(user=request.user)

    return render(request, 'messaging/conversation_form.html', {'form': form})


@require_POST
@login_required
def archive(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk)
    if not user_can_access_conversation(request.user, conversation):
        messages.error(request, 'You do not have access to this conversation.')
        return redirect('messaging:inbox')
    archive_conversation(conversation, request.user, archived=True)
    messages.success(request, 'Conversation archived for your account.')
    return redirect('messaging:inbox')


@require_POST
@login_required
def unarchive(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk)
    if not ConversationParticipant.objects.filter(conversation=conversation, user=request.user).exists():
        messages.error(request, 'You do not have access to this conversation.')
        return redirect('messaging:inbox')
    archive_conversation(conversation, request.user, archived=False)
    messages.success(request, 'Conversation moved back to your inbox.')
    return redirect('messaging:conversation_detail', pk=conversation.pk)


@require_POST
@login_required
def leave(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk)
    if not user_can_access_conversation(request.user, conversation):
        messages.error(request, 'You do not have access to this conversation.')
        return redirect('messaging:inbox')
    if conversation.conversation_type == Conversation.ConversationType.DIRECT:
        messages.error(request, 'Direct conversations cannot be left. You can archive them instead.')
        return redirect('messaging:conversation_detail', pk=conversation.pk)
    leave_conversation(conversation, request.user)
    messages.success(request, 'You left the conversation.')
    return redirect('messaging:inbox')


@require_POST
@login_required
def delete_message(request, pk):
    message = get_object_or_404(Message.objects.select_related('conversation'), pk=pk)
    if message.sender != request.user and not request.user.is_superuser:
        messages.error(request, 'You can only delete your own messages.')
        return redirect('messaging:conversation_detail', pk=message.conversation.pk)
    if not user_can_access_conversation(request.user, message.conversation):
        messages.error(request, 'You do not have access to this conversation.')
        return redirect('messaging:inbox')
    message.deleted_at = timezone.now()
    message.save(update_fields=['deleted_at'])
    messages.success(request, 'Message deleted.')
    return redirect('messaging:conversation_detail', pk=message.conversation.pk)
