from django.db import models
from django.core.validators import MinValueValidator
from users.models import User
from properties.models import Property, PropertyExtra


class Cart(models.Model):
    traveller = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='cart'
    )
    booking_property = models.ForeignKey(
        Property,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    check_in  = models.DateField(null=True, blank=True)
    check_out = models.DateField(null=True, blank=True)
    guests    = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart - {self.traveller.username}"

    @property
    def nights(self):
        if self.check_in and self.check_out:
            return (self.check_out - self.check_in).days
        return 0

    @property
    def room_total(self):
        if self.booking_property and self.nights > 0:
            return self.booking_property.price_per_night * self.nights
        return 0

    @property
    def extras_total(self):
        total = 0
        for item in self.items.all():
            if item.extra.charge_type == 'per_night':
                total += item.extra.price * self.nights
            elif item.extra.charge_type == 'once':
                total += item.extra.price
            elif item.extra.charge_type == 'per_person':
                total += item.extra.price * self.guests
        return total

    @property
    def grand_total(self):
        return self.room_total + self.extras_total


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    extra = models.ForeignKey(
        PropertyExtra,
        on_delete=models.CASCADE
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['cart', 'extra']

    @property
    def line_total(self):
        """Calculated cost for this extra based on charge type."""
        if self.extra.charge_type == 'per_night':
            return self.extra.price * self.cart.nights
        elif self.extra.charge_type == 'per_person':
            return self.extra.price * self.cart.guests
        return self.extra.price

    def __str__(self):
        return f"{self.extra.name} in {self.cart}"


class Booking(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    traveller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    booking_property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    check_in  = models.DateField()
    check_out = models.DateField()
    guests    = models.PositiveIntegerField(default=1)

    # Pricing snapshot at booking time
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    nights          = models.PositiveIntegerField()
    room_total      = models.DecimalField(max_digits=10, decimal_places=2)
    extras_total    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total     = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    reference  = models.CharField(max_length=20, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Booking {self.reference} - {self.traveller.username}"

    class Meta:
        ordering = ['-created_at']


class BookingExtra(models.Model):
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='extras'
    )
    extra_name  = models.CharField(max_length=100)
    extra_price = models.DecimalField(max_digits=8, decimal_places=2)
    charge_type = models.CharField(max_length=20)
    subtotal    = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.extra_name} for Booking {self.booking.reference}"