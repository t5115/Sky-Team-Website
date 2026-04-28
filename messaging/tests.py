from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Conversation, ConversationParticipant, Message
from .services import get_or_create_direct_conversation, send_message, unread_count_for_conversation

User = get_user_model()


class MessagingServiceTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username='alice', email='alice@example.com', password='pass12345')
        self.bob = User.objects.create_user(username='bob', email='bob@example.com', password='pass12345')

    def test_direct_conversation_is_reused(self):
        first, created_first = get_or_create_direct_conversation(self.alice, self.bob)
        second, created_second = get_or_create_direct_conversation(self.bob, self.alice)

        self.assertTrue(created_first)
        self.assertFalse(created_second)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(first.participant_links.count(), 2)

    def test_message_can_only_be_sent_by_participant(self):
        conversation, _ = get_or_create_direct_conversation(self.alice, self.bob)
        message = send_message(conversation, self.alice, 'Hello Bob')

        self.assertEqual(message.sender, self.alice)
        self.assertEqual(conversation.messages.count(), 1)
        self.assertEqual(unread_count_for_conversation(conversation, self.bob), 1)

    def test_empty_message_is_rejected(self):
        conversation, _ = get_or_create_direct_conversation(self.alice, self.bob)
        with self.assertRaises(Exception):
            send_message(conversation, self.alice, '   ')
