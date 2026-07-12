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

class LoginActivity(models.Model):
    """Tracks every login attempt (success or failure) for security review
    and brute-force lockout — the user field is nullable since failed
    attempts with an unknown/invalid username still get logged by IP."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True,
        related_name='login_activity'
    )
    username_attempted = models.CharField(max_length=150, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    success = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Login activity'

    def __str__(self):
        who = self.user.username if self.user else self.username_attempted
        return f"{'✔' if self.success else '✘'} {who} @ {self.created_at:%Y-%m-%d %H:%M}"
