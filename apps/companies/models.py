from django.db import models


class Company(models.Model):
    TYPE_CHOICES = [
        ('hotel', 'Hotel'),
        ('spa', 'Spa / Wellness'),
        ('retailer', 'Retailer'),
        ('events', 'Events Company'),
        ('corporate', 'Corporate'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='other')
    phone = models.CharField(max_length=25, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Companies'

    def __str__(self):
        return self.name
