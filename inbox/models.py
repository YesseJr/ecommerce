from django.db import models
from users.models import User
from properties.models import Property


class Conversation(models.Model):
    """One thread per (guest, property) pair — mirrors how Airbnb/Booking
    scope messaging to a specific stay rather than a raw DM system."""
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name='conversations'
    )
    guest = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='guest_conversations'
    )
    host = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='host_conversations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['property', 'guest']
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.guest.username} ↔ {self.host.username} · {self.property.name}"

    def other_party(self, user):
        return self.host if user == self.guest else self.guest

    def last_message(self):
        return self.messages.order_by('-created_at').first()

    def unread_count_for(self, user):
        return self.messages.filter(is_read=False).exclude(sender=user).count()


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name='messages'
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username}: {self.body[:40]}"


class Notification(models.Model):
    TYPES = [
        ('booking',      'Booking Update'),
        ('message',      'New Message'),
        ('payment',      'Payment'),
        ('review',       'Review'),
        ('system',       'System'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notif_type = models.CharField(max_length=20, choices=TYPES, default='system')
    title = models.CharField(max_length=150)
    body = models.CharField(max_length=250, blank=True)
    link = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.user.username}] {self.title}"

    @classmethod
    def send(cls, user, title, body='', link='', notif_type='system'):
        return cls.objects.create(
            user=user, title=title, body=body, link=link, notif_type=notif_type
        )
