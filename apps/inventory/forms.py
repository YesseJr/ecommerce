from django import forms
from .models import Fragrance
class FragranceForm(forms.ModelForm):
    class Meta:
        model = Fragrance
        fields = ['name', 'brand', 'sku', 'concentration', 'bottle_size', 'price', 'cost_price', 'stock_quantity', 'reorder_level', 'supplier', 'description', 'is_active']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}
