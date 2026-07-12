from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags


VERIFY_SALT = 'users.email-verification'
VERIFY_MAX_AGE = 60 * 60 * 48  # 48 hours


def get_client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


# ─── Email verification tokens ─────────────────────────────────────────────

def make_verification_token(user):
    return signing.dumps({'uid': user.pk}, salt=VERIFY_SALT)


def read_verification_token(token, max_age=VERIFY_MAX_AGE):
    """Returns the user id if the token is valid and unexpired, else None."""
    try:
        data = signing.loads(token, salt=VERIFY_SALT, max_age=max_age)
        return data.get('uid')
    except signing.BadSignature:
        return None


def send_verification_email(request, user):
    token = make_verification_token(user)
    path = reverse('users:verify_email', kwargs={'token': token})
    link = request.build_absolute_uri(path)

    subject = f"Verify your {settings.SITE_NAME} account"
    html_body = render_to_string('users/email/verify_email.html', {
        'user': user, 'link': link, 'site_name': settings.SITE_NAME,
    })
    send_mail(
        subject=subject,
        message=strip_tags(html_body),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_body,
        fail_silently=True,
    )


def send_password_changed_notice(user):
    subject = f"Your {settings.SITE_NAME} password was changed"
    html_body = render_to_string('users/email/password_changed.html', {
        'user': user, 'site_name': settings.SITE_NAME,
    })
    send_mail(
        subject=subject,
        message=strip_tags(html_body),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_body,
        fail_silently=True,
    )


# ─── Login lockout ──────────────────────────────────────────────────────────

def record_login_attempt(request, user=None, username_attempted='', success=False):
    from .models import LoginActivity
    LoginActivity.objects.create(
        user=user,
        username_attempted=username_attempted,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:300],
        success=success,
    )


def is_locked_out(request, username):
    """Checks recent failed attempts for this username+IP combo."""
    from .models import LoginActivity
    window_start = timezone.now() - timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
    ip = get_client_ip(request)
    failed_count = LoginActivity.objects.filter(
        username_attempted__iexact=username,
        ip_address=ip,
        success=False,
        created_at__gte=window_start,
    ).count()
    return failed_count >= settings.LOGIN_MAX_ATTEMPTS
