from django.db import models


class Fragrance(models.Model):
    CONCENTRATION_CHOICES = [
        ('edc', 'Eau de Cologne (EDC)'),
        ('edt', 'Eau de Toilette (EDT)'),
        ('edp', 'Eau de Parfum (EDP)'),
        ('parfum', 'Parfum / Extrait'),
    ]
    BOTTLE_SIZE_CHOICES = [
        ('10ml', '10 ml'),
        ('30ml', '30 ml'),
        ('50ml', '50 ml'),
        ('75ml', '75 ml'),
        ('100ml', '100 ml'),
        ('200ml', '200 ml'),
    ]

    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    concentration = models.CharField(max_length=10, choices=CONCENTRATION_CHOICES, default='edp')
    bottle_size = models.CharField(max_length=10, choices=BOTTLE_SIZE_CHOICES, default='50ml')
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text='Selling price (TZS)')
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, help_text='Cost / purchase price')
    stock_quantity = models.IntegerField(default=0)
    reorder_level = models.IntegerField(default=10, help_text='Alert when stock drops to this level')
    supplier = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='fragrances/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['brand', 'name']

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.reorder_level

    @property
    def display_name(self):
        return f"{self.name} {self.bottle_size} {self.get_concentration_display()}"

    @property
    def margin(self):
        if self.cost_price and self.price:
            return round(((self.price - self.cost_price) / self.price) * 100, 1)
        return 0

    def __str__(self):
        return self.display_name
