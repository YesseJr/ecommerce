from django import forms
from .models import Property, PropertyExtra, DAR_NEIGHBORHOODS

_NEIGHBORHOOD_CHOICES = [('', 'Select an area…')] + DAR_NEIGHBORHOODS + [
    ('Other', [('other', 'Other (not listed — type below)')])
]
_KNOWN_NEIGHBORHOODS = {value for _, group in DAR_NEIGHBORHOODS for value, _ in group}


class PropertyForm(forms.ModelForm):
    neighborhood = forms.ChoiceField(
        choices=_NEIGHBORHOOD_CHOICES,
        required=False,
        label='Neighborhood',
        help_text="Dar es Salaam–wide — pick the closest area."
    )
    neighborhood_other = forms.CharField(
        required=False,
        label='Other area',
        widget=forms.TextInput(attrs={'placeholder': 'Type the area name…'})
    )

    class Meta:
        model = Property
        fields = [
            'name', 'property_type', 'description',
            'country', 'city', 'address',
            'price_per_night', 'max_guests',
            'bedrooms', 'bathrooms', 'is_available',
            'cancellation_policy', 'house_rules', 'accessibility_features',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'address': forms.Textarea(attrs={'rows': 2}),
            'house_rules': forms.Textarea(attrs={'rows': 3, 'placeholder': 'e.g. No smoking\nNo parties or events\nCheck-in after 2:00 PM'}),
            'accessibility_features': forms.Textarea(attrs={'rows': 3, 'placeholder': 'e.g. Step-free entrance\nElevator access\nWide doorways'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Default new listings to Dar es Salaam — the platform is city-wide.
        if not self.instance.pk and not self.initial.get('city'):
            self.fields['city'].initial = 'Dar es Salaam'

        # Pre-select the dropdown for existing instances; if the saved value
        # isn't one of the curated areas, fall back to "Other" + prefill it.
        current = self.instance.neighborhood if self.instance.pk else ''
        if current:
            if current in _KNOWN_NEIGHBORHOODS:
                self.fields['neighborhood'].initial = current
            else:
                self.fields['neighborhood'].initial = 'other'
                self.fields['neighborhood_other'].initial = current

    def clean(self):
        cleaned = super().clean()
        choice = cleaned.get('neighborhood')
        other  = cleaned.get('neighborhood_other', '').strip()
        cleaned['neighborhood'] = other if choice == 'other' and other else choice
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.neighborhood = self.cleaned_data.get('neighborhood', '')
        if commit:
            instance.save()
        return instance


class PropertyExtraForm(forms.ModelForm):
    class Meta:
        model = PropertyExtra
        fields = ['name', 'description', 'price', 'charge_type', 'is_available']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }