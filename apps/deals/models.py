from django.db import models
from django.conf import settings


class Deal(models.Model):
    STAGE_LEAD = 'lead'
    STAGE_QUALIFIED = 'qualified'
    STAGE_PROPOSAL = 'proposal'
    STAGE_NEGOTIATION = 'negotiation'
    STAGE_WON = 'won'
    STAGE_LOST = 'lost'
    STAGE_CHOICES = [
        (STAGE_LEAD, 'Lead'),
        (STAGE_QUALIFIED, 'Qualified'),
        (STAGE_PROPOSAL, 'Proposal Sent'),
        (STAGE_NEGOTIATION, 'Negotiation'),
        (STAGE_WON, 'Won'),
        (STAGE_LOST, 'Lost'),
    ]
    SOURCE_CHOICES = [
        ('walk_in', 'Walk-in'),
        ('referral', 'Referral'),
        ('online', 'Online'),
        ('email', 'Email'),
        ('social', 'Social Media'),
        ('event', 'Event'),
    ]

    title = models.CharField(max_length=200)
    contact = models.ForeignKey(
        'contacts.Contact', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='deals'
    )
    company = models.ForeignKey(
        'companies.Company', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='deals'
    )
    value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default=STAGE_LEAD)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_deals'
    )
    expected_close = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def is_active(self):
        return self.stage not in [self.STAGE_WON, self.STAGE_LOST]

    @property
    def days_in_stage(self):
        from django.utils import timezone
        delta = timezone.now() - self.updated_at
        return delta.days

    def __str__(self):
        return self.title
