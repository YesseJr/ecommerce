from django import forms
from .models import Lead
class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ['contact', 'name', 'email', 'phone', 'source', 'status', 'assigned_to', 'notes']
        widgets = {'notes': forms.Textarea(attrs={'rows': 3})}
