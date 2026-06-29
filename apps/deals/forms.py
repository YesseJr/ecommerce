from django import forms
from .models import Deal
class DealForm(forms.ModelForm):
    class Meta:
        model = Deal
        fields = ['title', 'contact', 'company', 'value', 'stage', 'source', 'assigned_to', 'expected_close', 'notes']
        widgets = {'notes': forms.Textarea(attrs={'rows': 3}), 'expected_close': forms.DateInput(attrs={'type': 'date'})}
