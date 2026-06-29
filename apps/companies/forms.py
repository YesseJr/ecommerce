from django import forms
from .models import Company
class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'type', 'phone', 'email', 'city', 'address', 'website', 'notes']
        widgets = {'notes': forms.Textarea(attrs={'rows': 3}), 'address': forms.Textarea(attrs={'rows': 2})}
