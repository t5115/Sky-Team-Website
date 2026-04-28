from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Max, Q
from django.utils import timezone

from teams.models import TeamMembership

from .models import Conversation, ConversationParticipant, Message, MessageReadReceipt

User = get_user_model()


def user_can_access_conversation(user, conversation):
    if not user.is_authenticated:
        return False
    return ConversationParticipant.objects.filter(
        conversation=conversation,
        user=user,
        left_at__isnull=True,
    ).exists()


def get_user_conversations(user, include_archived=False):
    links = ConversationParticipant.objects.filter(user=user, left_at__isnull=True)
    if not include_archived:
        links = links.filter(is_archived=False)
    conversation_ids = links.values_list('conversation_id', flat=True)
    return (
        Conversation.objects.filter(pk__in=conversation_ids)
        .select_related('team', 'created_by')
        .prefetch_related('participant_links__user', 'messages')
        .annotate(last_message_at=Max('messages__sent_at'))
        .order_by('-updated_at')
    )


def get_or_create_direct_conversation(current_user, other_user):
    """Reuse the existing 1-to-1 conversation if it already exists."""
    if current_user == other_user:
        raise ValueError('You cannot start a direct conversation with yourself.')

    existing = (
        Conversation.objects
        .filter(conversation_type=Conversation.ConversationType.DIRECT)
        .annotate(total_participants=Count('participant_links', filter=Q(participant_links__left_at__isnull=True)))
        .filter(total_participants=2, participant_links__user=current_user)
        .filter(participant_links__user=other_user)
        .first()
    )
    if existing:
        return existing, False

    with transaction.atomic():
        conversation = Conversation.objects.create(
            conversation_type=Conversation.ConversationType.DIRECT,
            created_by=current_user,
        )
        ConversationParticipant.objects.create(conversation=conversation, user=current_user, role=ConversationParticipant.Role.ADMIN)
        ConversationParticipant.objects.create(conversation=conversation, user=other_user)
    return conversation, True


def create_group_conversation(created_by, title, users, team=None):
    users = list(dict.fromkeys(users))
    if created_by not in users:
        users.append(created_by)
    if len(users) < 2:
        raise ValueError('A conversation needs at least two participants.')

    conversation_type = Conversation.ConversationType.TEAM if team else Conversation.ConversationType.GROUP
    with transaction.atomic():
        conversation = Conversation.objects.create(
            title=title,
            conversation_type=conversation_type,
            team=team,
            created_by=created_by,
        )
        for user in users:
            ConversationParticipant.objects.create(
                conversation=conversation,
                user=user,
                role=ConversationParticipant.Role.ADMIN if user == created_by else ConversationParticipant.Role.MEMBER,
            )
    return conversation


def get_active_team_users(team):
    return User.objects.filter(
        person_profile__team_memberships__team=team,
        person_profile__team_memberships__left_at__isnull=True,
        is_active=True,
    ).distinct().order_by('username')


def send_message(conversation, sender, body, attachment_url=''):
    if not user_can_access_conversation(sender, conversation):
        raise PermissionError('User is not part of this conversation.')
    message = Message.objects.create(
        conversation=conversation,
        sender=sender,
        body=body,
        attachment_url=attachment_url,
    )
    # A new message should bring the thread back into each active participant's inbox.
    ConversationParticipant.objects.filter(
        conversation=conversation,
        left_at__isnull=True,
    ).update(is_archived=False)
    mark_conversation_read(conversation, sender)
    return message


def mark_conversation_read(conversation, user):
    now = timezone.now()
    ConversationParticipant.objects.filter(conversation=conversation, user=user).update(last_read_at=now)
    unread_messages = conversation.messages.exclude(sender=user).filter(deleted_at__isnull=True)
    existing = MessageReadReceipt.objects.filter(user=user, message__conversation=conversation).values_list('message_id', flat=True)
    receipts = [MessageReadReceipt(message=message, user=user) for message in unread_messages.exclude(pk__in=existing)]
    MessageReadReceipt.objects.bulk_create(receipts, ignore_conflicts=True)


def unread_count_for_conversation(conversation, user):
    link = ConversationParticipant.objects.filter(conversation=conversation, user=user).first()
    if not link or not link.last_read_at:
        return conversation.messages.exclude(sender=user).filter(deleted_at__isnull=True).count()
    return conversation.messages.exclude(sender=user).filter(deleted_at__isnull=True, sent_at__gt=link.last_read_at).count()


def archive_conversation(conversation, user, archived=True):
    ConversationParticipant.objects.filter(conversation=conversation, user=user).update(is_archived=archived)


def leave_conversation(conversation, user):
    ConversationParticipant.objects.filter(conversation=conversation, user=user).update(left_at=timezone.now())
