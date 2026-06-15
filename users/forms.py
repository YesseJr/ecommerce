from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class RegisterForm(UserCreationForm):

    ROLE_CHOICES = [
        ('traveller', 'I am a Traveller — looking for accommodation'),
        ('owner', 'I am a Property Owner — I want to list my property'),
    ]

    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Email Address'})
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Phone Number (optional)'})
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect,
        initial='traveller',    # ✅ Traveller pre-selected by default
    )

    class Meta:
        model  = User
        fields = [
            'first_name', 'last_name', 'username',
            'email', 'phone', 'role',
            'password1', 'password2'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data.get('phone', '')
        user.role  = self.cleaned_data['role']
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model  = User
        fields = [
            'first_name', 'last_name',
            'email', 'phone',
            'bio', 'location',
            'profile_photo'
        ]