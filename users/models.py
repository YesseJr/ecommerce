from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    ROLE_CHOICES = [
        ('traveller', 'Traveller'),
        ('owner', 'Property Owner'),
        ('admin', 'Admin'),
    ]

    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default='traveller'
    )
    phone = models.CharField(max_length=20, blank=True)
    profile_photo = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True
    )
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Superusers always get admin role — no exceptions
        if self.is_superuser:
            self.role = 'admin'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_traveller(self):
        # Superusers are never travellers
        if self.is_superuser:
            return False
        return self.role == 'traveller'

    @property
    def is_owner(self):
        # Superusers are never owners
        if self.is_superuser:
            return False
        return self.role == 'owner'

    @property
    def is_admin(self):
        # Either superuser OR role set to admin
        return self.is_superuser or self.role == 'admin'