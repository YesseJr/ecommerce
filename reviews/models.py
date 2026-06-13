from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import User
from properties.models import Property
from bookings.models import Booking


class Review(models.Model):
    # Only travellers who completed a booking can review
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='review'
    )
    traveller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    # Ratings (1-5)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    cleanliness = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    location = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    value = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    title = models.CharField(max_length=200)
    comment = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.traveller.username} - {self.property.name}"

    class Meta:
        ordering = ['-created_at']