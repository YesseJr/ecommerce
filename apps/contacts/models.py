from django.db import models
from django.conf import settings


class Contact(models.Model):
    STATUS_VIP = 'vip'
    STATUS_ACTIVE = 'active'
    STATUS_NEW = 'new'
    STATUS_INACTIVE = 'inactive'
    STATUS_CHOICES = [
        (STATUS_VIP, 'VIP'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_NEW, 'New'),
        (STATUS_INACTIVE, 'Inactive'),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=25)
    city = models.CharField(max_length=100, blank=True)
    loyalty_points = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='contacts_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def initials(self):
        return (
            (self.first_name[0] if self.first_name else '') +
            (self.last_name[0] if self.last_name else '')
        ).upper()

    @property
    def lifetime_value(self):
        from django.db.models import Sum
        return self.sale_set.filter(status='completed').aggregate(
            total=Sum('total')
        )['total'] or 0

    def __str__(self):
        return self.full_name
