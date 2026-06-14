from django import forms
from .models import Review


class ReviewForm(forms.ModelForm):

    RATING_CHOICES = [(i, i) for i in range(1, 6)]

    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect,
        label='Overall Rating'
    )
    cleanliness = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect
    )
    location = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect
    )
    value = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect
    )

    class Meta:
        model  = Review
        fields = [
            'rating', 'cleanliness',
            'location', 'value',
            'title', 'comment'
        ]
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4}),
        }