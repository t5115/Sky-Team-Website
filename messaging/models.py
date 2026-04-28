from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Conversation(models.Model):
    """
    A private or group conversation between application users.

    Production-style decisions:
    - Conversations are kept even if users archive them, because messages are audit history.
    - A direct conversation is limited to exactly two active participants.
    - A team conversation can optionally be linked to a Team.
    """

    class ConversationType(models.TextChoices):
        DIRECT = 'direct', 'Direct message'
        GROUP = 'group', 'Group chat'
        TEAM = 'team', 'Team chat'

    title = models.CharField(max_length=180, blank=True)
    conversation_type = models.CharField(
        max_length=20,
        choices=ConversationType.choices,
        default=ConversationType.DIRECT,
    )
    team = models.ForeignKey(
        'teams.Team',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_conversations',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['conversation_type', 'updated_at']),
            models.Index(fields=['team', 'updated_at']),
        ]

    def __str__(self):
        return self.display_title

    @property
    def display_title(self):
        if self.title:
            return self.title
        if self.conversation_type == self.ConversationType.TEAM and self.team:
            return f'{self.team.name} team chat'
        return 'Direct conversation'

    def clean(self):
        super().clean()
        if self.title:
            self.title = self.title.strip()
        if self.conversation_type == self.ConversationType.TEAM and not self.team:
            raise ValidationError({'team': 'A team conversation must be linked to a team.'})
        if self.conversation_type != self.ConversationType.TEAM and self.team:
            raise ValidationError({'team': 'Only team conversations can be linked to a team.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class ConversationParticipant(models.Model):
    """
    Links a User to a Conversation with per-user state.

    This is how real messaging systems support inbox state without changing the
    conversation for everyone: unread time, archive, mute, role, and leaving.
    """

    class Role(models.TextChoices):
        MEMBER = 'member', 'Member'
        ADMIN = 'admin', 'Admin'

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='participant_links',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversation_links',
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    last_read_at = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    is_muted = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['conversation', 'user'],
                name='unique_conversation_user_participant',
            ),
        ]
        indexes = [
            models.Index(fields=['user', 'is_archived', 'left_at']),
            models.Index(fields=['conversation', 'left_at']),
        ]
        ordering = ['joined_at']

    def __str__(self):
        return f'{self.user} in {self.conversation}'

    @property
    def is_active(self):
        return self.left_at is None


class Message(models.Model):
    """
    One message inside a conversation.

    Messages are soft-deleted instead of physically removed. This keeps the
    thread consistent for other participants and gives a basic audit trail.
    """

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='sent_messages',
    )
    body = models.TextField(max_length=5000)
    attachment_url = models.URLField(blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['sent_at']
        indexes = [
            models.Index(fields=['conversation', 'sent_at']),
            models.Index(fields=['sender', 'sent_at']),
        ]

    def __str__(self):
        return f'Message from {self.sender} at {self.sent_at}'

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    @property
    def safe_body(self):
        if self.is_deleted:
            return 'This message was deleted.'
        return self.body

    def clean(self):
        super().clean()
        if self.body is not None:
            self.body = self.body.strip()
        if self.attachment_url is not None:
            self.attachment_url = self.attachment_url.strip()
        if not self.body and not self.attachment_url:
            raise ValidationError('A message must contain text or an attachment link.')
        if self.attachment_url and not self.attachment_url.startswith(('http://', 'https://')):
            raise ValidationError({'attachment_url': 'Attachment link must start with http:// or https://.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        Conversation.objects.filter(pk=self.conversation_id).update(updated_at=timezone.now())


class MessageReadReceipt(models.Model):
    """Stores exactly when each user read each message."""

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_receipts')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='message_read_receipts')
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['message', 'user'], name='unique_message_read_receipt'),
        ]
        indexes = [
            models.Index(fields=['user', 'read_at']),
        ]

    def __str__(self):
        return f'{self.user} read message {self.message_id}'
