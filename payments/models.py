from django.db import models
from users.models import User
from bookings.models import Booking


class CurrencyConfig(models.Model):
    """
    Singleton model to manage exchange rates.
    Admin can update the rate via Django admin panel.
    """
    usd_to_tzs = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=2500.00,
        help_text="Exchange rate: 1 USD = this many TZS"
    )
    usd_enabled = models.BooleanField(default=True, help_text="Allow payments in USD")
    tzs_enabled = models.BooleanField(default=True, help_text="Allow payments in TZS (Tanzanian Shilling)")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Currency Configuration"
        verbose_name_plural = "Currency Configuration"

    def __str__(self):
        return f"1 USD = {self.usd_to_tzs} TZS (Updated: {self.updated_at.strftime('%d %b %Y %H:%M') if self.updated_at else 'Never'})"

    @classmethod
    def get_config(cls):
        """Return the singleton config, creating it if it doesn't exist."""
        obj, _ = cls.objects.get_or_create(pk=1, defaults={'usd_to_tzs': 2500.00})
        return obj

    @classmethod
    def get_rate(cls):
        """Return the current USD→TZS exchange rate."""
        return cls.get_config().usd_to_tzs


class Payment(models.Model):

    METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('mpesa', 'M-Pesa'),
        ('airtel', 'Airtel Money'),
        ('tigo', 'Tigo Pesa'),
        ('halopesa', 'HaloPesa'),
        # Legacy choices kept for backward compatibility with existing data
        ('card', 'Card (Legacy)'),
        ('cash', 'Cash on Arrival'),
        ('mix', 'Mixed Payment'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Successful'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled (no refund)'),
    ]

    CURRENCY_CHOICES = [
        ('USD', 'US Dollar (USD)'),
        ('TZS', 'Tanzanian Shilling (TZS)'),
    ]

    booking = models.OneToOneField(
        Booking, on_delete=models.CASCADE, related_name='payment'
    )
    traveller = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='payments'
    )

    # --- Payment Method ---
    payment_method = models.CharField(
        max_length=20, choices=METHOD_CHOICES, default='mpesa'
    )
    provider = models.CharField(
        max_length=50, blank=True,
        help_text="Mobile money provider (M-Pesa, Airtel...) or card network"
    )

    # --- Currency & Amounts ---
    currency = models.CharField(
        max_length=3, choices=CURRENCY_CHOICES, default='USD'
    )
    exchange_rate = models.DecimalField(
        max_digits=10, decimal_places=2, default=1.00,
        help_text="Exchange rate applied at payment time (USD to selected currency)"
    )
    amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text="Charged amount in the selected currency"
    )
    amount_usd = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Equivalent amount in USD"
    )

    # --- Transaction References ---
    transaction_id = models.CharField(max_length=100, unique=True, blank=True)
    authorization_code = models.CharField(
        max_length=50, blank=True, help_text="Card authorization code"
    )
    receipt_number = models.CharField(
        max_length=50, blank=True, help_text="Mobile money receipt number"
    )

    # --- Status ---
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending'
    )

    # --- Timestamps ---
    payment_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    # ---------- Helpers ----------

    def is_mobile_money(self):
        return self.payment_method in ('mpesa', 'airtel', 'tigo', 'halopesa')

    def is_card(self):
        return self.payment_method in ('credit_card', 'debit_card', 'card')

    def get_currency_symbol(self):
        return 'TSh' if self.currency == 'TZS' else '$'

    def get_formatted_amount(self):
        symbol = self.get_currency_symbol()
        if self.currency == 'TZS':
            return f"{symbol} {self.amount:,.0f}"
        return f"{symbol}{self.amount:,.2f}"

    # ---------- Legacy compat ----------
    @property
    def paid_at(self):
        """Legacy compatibility: templates that reference paid_at still work."""
        return self.payment_date

    @property
    def method(self):
        """Legacy compatibility."""
        return self.payment_method

    def get_method_display(self):
        return dict(self.METHOD_CHOICES).get(self.payment_method, self.payment_method)

    def __str__(self):
        return f"Payment {self.transaction_id} — {self.status}"


class Coupon(models.Model):
    """Promo codes — percentage or fixed-amount discounts on bookings."""

    DISCOUNT_TYPES = [
        ('percent', 'Percentage'),
        ('fixed', 'Fixed Amount (USD)'),
    ]

    code = models.CharField(max_length=30, unique=True)
    description = models.CharField(max_length=200, blank=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES, default='percent')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_booking_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_uses = models.PositiveIntegerField(default=0, help_text="0 = unlimited")
    used_count = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.code

    def is_valid(self, amount=None):
        from django.utils import timezone
        now = timezone.now()
        if not self.active:
            return False, "This coupon is no longer active."
        if now < self.valid_from:
            return False, "This coupon isn't active yet."
        if now > self.valid_to:
            return False, "This coupon has expired."
        if self.max_uses and self.used_count >= self.max_uses:
            return False, "This coupon has reached its usage limit."
        if amount is not None and amount < self.min_booking_amount:
            return False, f"Minimum booking amount for this coupon is ${self.min_booking_amount}."
        return True, ""

    def calculate_discount(self, amount):
        if self.discount_type == 'percent':
            return round(amount * (self.discount_value / 100), 2)
        return min(self.discount_value, amount)
