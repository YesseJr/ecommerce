import random
import string
from django.db import models
from django.conf import settings


def generate_reference():
    digits = ''.join(random.choices(string.digits, k=4))
    return f"EL-{digits}"


class Sale(models.Model):
    PAYMENT_CASH = 'cash'
    PAYMENT_MPESA = 'mpesa'
    PAYMENT_CARD = 'card'
    PAYMENT_CHOICES = [
        (PAYMENT_CASH, 'Cash'),
        (PAYMENT_MPESA, 'M-Pesa'),
        (PAYMENT_CARD, 'Card'),
    ]
    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('refunded', 'Refunded'),
        ('voided', 'Voided'),
    ]

    reference = models.CharField(max_length=20, unique=True, editable=False)
    contact = models.ForeignKey(
        'contacts.Contact', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='sales'
    )
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default=PAYMENT_CASH)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.reference:
            ref = generate_reference()
            while Sale.objects.filter(reference=ref).exists():
                ref = generate_reference()
            self.reference = ref
        super().save(*args, **kwargs)

    def __str__(self):
        return self.reference


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, related_name='items', on_delete=models.CASCADE)
    fragrance = models.ForeignKey('inventory.Fragrance', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.sale.reference} — {self.fragrance.name} ×{self.quantity}"
