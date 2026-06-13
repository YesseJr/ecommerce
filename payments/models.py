from django.db import models
from users.models import User
from bookings.models import Booking


class Payment(models.Model):

    METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('card', 'Debit/Credit Card'),
        ('airtel', 'Airtel Money'),
        ('cash', 'Cash'),
        ('mix', 'Mix by Yass'),
        ('halopesa', 'Halopesa'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='payment'
    )
    traveller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(
        max_length=20,
        choices=METHOD_CHOICES,
        default='mpesa'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # Simulated transaction reference
    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        blank=True
    )

    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.status}"