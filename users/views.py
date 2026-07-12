from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from .models import User
from .forms import RegisterForm, LoginForm, ProfileUpdateForm
from .utils import (
    send_verification_email, read_verification_token,
    record_login_attempt, is_locked_out,
)


def register_view(request):
    if request.user.is_authenticated:
        return redirect('properties:home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_verification_email(request, user)
            return render(request, 'users/registration_pending.html', {'email': user.email})
    else:
        form = RegisterForm()

    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('properties:home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            if is_locked_out(request, username):
                messages.error(
                    request,
                    f"Too many failed attempts. Please try again in "
                    f"{settings.LOGIN_LOCKOUT_MINUTES} minutes."
                )
                return render(request, 'users/login.html', {'form': form})

            user = authenticate(request, username=username, password=password)

            if user is not None:
                if not user.is_verified and not user.is_staff and not user.is_superuser:
                    record_login_attempt(request, user=user, username_attempted=username, success=False)
                    messages.error(request, "Please verify your email before logging in.")
                    return render(request, 'users/login.html', {
                        'form': form,
                        'unverified_email': user.email,
                    })

                login(request, user)
                record_login_attempt(request, user=user, username_attempted=username, success=True)
                messages.success(request, f"Welcome back, {user.first_name}! 👋")

                # Redirect based on role
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                if user.is_owner:
                    return redirect('properties:owner_dashboard')
                elif user.is_traveller:
                    return redirect('properties:traveller_dashboard')
                return redirect('properties:home')
            else:
                record_login_attempt(request, user=None, username_attempted=username, success=False)
                messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()

    return render(request, 'users/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You've been logged out. See you soon! 👋")
    return redirect('properties:home')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully! ✅")
            return redirect('users:profile')
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, 'users/profile.html', {'form': form})

def verify_email(request, token):
    uid = read_verification_token(token)
    if uid is None:
        messages.error(request, "That verification link is invalid or has expired. Request a new one below.")
        return redirect('users:resend_verification_public')

    try:
        target_user = User.objects.get(pk=uid)
    except User.DoesNotExist:
        messages.error(request, "That verification link doesn't match any account.")
        return redirect('users:resend_verification_public')

    if target_user.is_verified:
        messages.info(request, "This email is already verified — you can log in.")
    else:
        target_user.is_verified = True
        target_user.save(update_fields=['is_verified'])
        messages.success(request, "Email verified! ✅ You can now log in.")

    return redirect('users:login')


def resend_verification_public(request):
    """Public resend page — works for logged-out users, doesn't reveal
    whether a given email exists (avoids account enumeration)."""
    prefill_email = request.GET.get('email', '')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        user = User.objects.filter(email__iexact=email).first()
        if user and not user.is_verified:
            send_verification_email(request, user)
        messages.success(
            request,
            "If that email belongs to an unverified account, we've sent a new verification link."
        )
        return redirect('users:login')

    return render(request, 'users/resend_verification.html', {'prefill_email': prefill_email})


@login_required
def resend_verification(request):
    if request.user.is_verified:
        messages.info(request, "Your email is already verified.")
    else:
        send_verification_email(request, request.user)
        messages.success(request, "Verification email sent — check your inbox.")
    return redirect('users:profile')


@login_required
def login_activity_view(request):
    activity = request.user.login_activity.all()[:25]
    return render(request, 'users/login_activity.html', {'activity': activity})
