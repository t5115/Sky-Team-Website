from django.contrib import admin

from .models import Conversation, ConversationParticipant, Message, MessageReadReceipt


class ConversationParticipantInline(admin.TabularInline):
    model = ConversationParticipant
    extra = 0
    autocomplete_fields = ['user']


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ['sent_at', 'edited_at', 'deleted_at']
    autocomplete_fields = ['sender']


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['display_title', 'conversation_type', 'team', 'created_by', 'updated_at']
    list_filter = ['conversation_type', 'created_at', 'updated_at']
    search_fields = ['title', 'team__name', 'created_by__username', 'created_by__email']
    autocomplete_fields = ['created_by', 'team']
    inlines = [ConversationParticipantInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'sender', 'sent_at', 'deleted_at']
    list_filter = ['sent_at', 'deleted_at']
    search_fields = ['body', 'sender__username', 'sender__email']
    autocomplete_fields = ['conversation', 'sender']


@admin.register(MessageReadReceipt)
class MessageReadReceiptAdmin(admin.ModelAdmin):
    list_display = ['message', 'user', 'read_at']
    autocomplete_fields = ['message', 'user']
