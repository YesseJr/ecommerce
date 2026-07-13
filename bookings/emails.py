"""
Booking lifecycle emails — confirmation (sent immediately on payment),
welcome (sent the morning of check-in), and goodbye (sent the morning of
check-out). Each sender is idempotent: it checks + sets a *_email_sent
flag on the Booking so re-running the daily command never double-sends.
"""
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def _send(booking, template_name, subject, mark_field):
    guest = booking.traveller
    prop = booking.booking_property

    html_body = render_to_string(f'bookings/email/{template_name}', {
        'booking': booking,
        'guest': guest,
        'property': prop,
        'site_name': settings.SITE_NAME,
    })

    send_mail(
        subject=subject,
        message=strip_tags(html_body),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[guest.email],
        html_message=html_body,
        fail_silently=True,
    )

    setattr(booking, mark_field, True)
    booking.save(update_fields=[mark_field])


def send_booking_confirmation_email(booking):
    if booking.confirmation_email_sent:
        return
    _send(
        booking, 'booking_confirmation.html',
        f"Booking confirmed — {booking.booking_property.name}",
        'confirmation_email_sent',
    )


def send_welcome_email(booking):
    if booking.welcome_email_sent:
        return
    _send(
        booking, 'welcome_stay.html',
        f"Welcome to {booking.booking_property.name}! 🎉",
        'welcome_email_sent',
    )


def send_goodbye_email(booking):
    if booking.goodbye_email_sent:
        return
    from django.urls import reverse
    review_path = reverse('reviews:add_review', kwargs={'booking_reference': booking.reference})
    review_link = f"{settings.SITE_URL.rstrip('/')}{review_path}"

    guest = booking.traveller
    prop = booking.booking_property
    html_body = render_to_string('bookings/email/goodbye_stay.html', {
        'booking': booking, 'guest': guest, 'property': prop,
        'site_name': settings.SITE_NAME, 'review_link': review_link,
    })
    send_mail(
        subject=f"Thanks for staying at {prop.name}",
        message=strip_tags(html_body),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[guest.email],
        html_message=html_body,
        fail_silently=True,
    )
    booking.goodbye_email_sent = True
    booking.save(update_fields=['goodbye_email_sent'])


def run_daily_stay_email_sweep():
    """
    Shared entry point for the day-of-stay email sweep — used by both the
    `send_stay_emails` management command (cron/Task Scheduler) and the
    secured HTTP endpoint (for hosts without shell/cron access). Keeping
    one implementation means the two trigger paths can never drift apart.

    Returns a dict summary instead of printing, so both callers can format
    the result however suits them (console output vs JSON response).
    """
    from datetime import date
    from .models import Booking

    today = date.today()

    checking_in = Booking.objects.filter(
        status='confirmed', check_in=today, welcome_email_sent=False
    ).select_related('traveller', 'booking_property')

    checking_out = Booking.objects.filter(
        status='confirmed', check_out=today, goodbye_email_sent=False
    ).select_related('traveller', 'booking_property')

    welcome_refs, goodbye_refs = [], []

    for booking in checking_in:
        send_welcome_email(booking)
        welcome_refs.append(booking.reference)

    for booking in checking_out:
        send_goodbye_email(booking)
        goodbye_refs.append(booking.reference)

    return {
        'date': today.isoformat(),
        'welcome_sent': len(welcome_refs),
        'goodbye_sent': len(goodbye_refs),
        'welcome_refs': welcome_refs,
        'goodbye_refs': goodbye_refs,
    }
