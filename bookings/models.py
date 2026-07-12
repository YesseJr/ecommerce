from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
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
    children  = models.PositiveIntegerField(default=0)
    special_requests = models.TextField(blank=True)
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

    @property
    def service_fee(self):
        """Platform service fee — 5% of room + extras, shown itemized at checkout."""
        return round(self.grand_total * Decimal('0.05'), 2)

    @property
    def tax_amount(self):
        """Illustrative local tax — adjust to match actual applicable rates."""
        return round(self.grand_total * Decimal('0.03'), 2)

    def total_with_fees(self, discount=Decimal('0')):
        return round(self.grand_total + self.service_fee + self.tax_amount - discount, 2)


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
    adults    = models.PositiveIntegerField(default=1)
    children  = models.PositiveIntegerField(default=0)
    special_requests = models.TextField(blank=True)

    # Pricing snapshot at booking time
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    nights          = models.PositiveIntegerField()
    room_total      = models.DecimalField(max_digits=10, decimal_places=2)
    extras_total    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_fee     = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deposit_amount  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total     = models.DecimalField(max_digits=10, decimal_places=2)

    coupon = models.ForeignKey(
        'payments.Coupon',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='bookings'
    )

    # Cancellation policy snapshot (copied from the property at booking time
    # so a later policy change on the listing doesn't retroactively change
    # what a guest agreed to).
    cancellation_policy = models.CharField(max_length=20, blank=True, choices=[
        ('flexible', 'Flexible — full refund up to 24h before check-in'),
        ('moderate', 'Moderate — full refund up to 5 days before check-in'),
        ('strict',   'Strict — 50% refund up to 7 days before check-in'),
    ])
    cancelled_at         = models.DateTimeField(null=True, blank=True)
    cancellation_reason  = models.TextField(blank=True)
    refund_amount         = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

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

    @property
    def is_cancellable(self):
        return self.status in ('pending', 'confirmed')

    def calculate_refund(self):
        """
        Applies the cancellation policy snapshotted at booking time to
        determine the refund amount if cancelled today.
        """
        from datetime import date as _date
        days_before = (self.check_in - _date.today()).days
        policy = self.cancellation_policy or 'moderate'

        if policy == 'flexible':
            pct = 1.0 if days_before >= 1 else 0.0
        elif policy == 'strict':
            pct = 0.5 if days_before >= 7 else 0.0
        else:  # moderate
            pct = 1.0 if days_before >= 5 else 0.0

        refundable_base = self.grand_total - self.deposit_amount
        return round(float(refundable_base) * pct, 2)


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