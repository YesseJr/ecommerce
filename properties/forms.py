from django import forms
from .models import Property, PropertyExtra


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = [
            'name', 'property_type', 'description',
            'country', 'city', 'address',
            'price_per_night', 'max_guests',
            'bedrooms', 'bathrooms', 'is_available',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }


class PropertyExtraForm(forms.ModelForm):
    class Meta:
        model = PropertyExtra
        fields = ['name', 'description', 'price', 'charge_type', 'is_available']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }