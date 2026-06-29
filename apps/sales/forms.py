from django import forms
from .models import Sale
class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['contact', 'payment_method', 'discount', 'notes']
        widgets = {'notes': forms.Textarea(attrs={'rows': 2})}
