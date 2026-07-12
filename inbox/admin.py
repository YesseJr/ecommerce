from django.contrib import admin
from .models import Conversation, Message, Notification


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['property', 'guest', 'host', 'updated_at']
    search_fields = ['property__name', 'guest__username', 'host__username']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'sender', 'created_at', 'is_read']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notif_type', 'title', 'is_read', 'created_at']
    list_filter = ['notif_type', 'is_read']
