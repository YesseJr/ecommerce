from django.db import models
from django.conf import settings


class Lead(models.Model):
    SOURCE_CHOICES = [
        ('walk_in', 'Walk-in'),
        ('referral', 'Referral'),
        ('online', 'Online'),
        ('social', 'Social Media'),
        ('email', 'Email Campaign'),
        ('event', 'Event'),
    ]
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('lost', 'Lost'),
    ]

    contact = models.ForeignKey(
        'contacts.Contact', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='leads'
    )
    name = models.CharField(max_length=200, blank=True, help_text='If not linked to a contact')
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=25, blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='walk_in')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    notes = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_leads'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='leads_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def display_name(self):
        if self.contact:
            return self.contact.full_name
        return self.name or self.email or 'Unknown Lead'

    def __str__(self):
        return self.display_name
