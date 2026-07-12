"""
Diagnostic command for the email pipeline (Brevo via django-anymail).

Usage:
    python manage.py test_email you@example.com

Prints exactly what's configured, attempts a real send, and reports a
clear success/failure reason instead of a raw traceback where possible.
"""
from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Sends a test email to diagnose the Brevo/Anymail configuration."

    def add_arguments(self, parser):
        parser.add_argument('to_email', type=str, help='Address to send the test email to')

    def handle(self, *args, **options):
        to_email = options['to_email']

        self.stdout.write(self.style.MIGRATE_HEADING("\n── Email configuration ──"))
        self.stdout.write(f"EMAIL_BACKEND:      {settings.EMAIL_BACKEND}")
        self.stdout.write(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

        key = getattr(settings, 'BREVO_API_KEY', '')
        if key:
            masked = key[:8] + '…' + key[-4:] if len(key) > 12 else '(set, short value)'
            self.stdout.write(f"BREVO_API_KEY:      {masked}  ({len(key)} chars)")
        else:
            self.stdout.write(self.style.WARNING(
                "BREVO_API_KEY:      NOT SET — using console backend, nothing will actually send."
            ))

        if 'anymail' not in settings.EMAIL_BACKEND:
            self.stdout.write(self.style.WARNING(
                "\nNote: EMAIL_BACKEND isn't the Brevo/Anymail backend right now, so this will "
                "just print to the console below rather than really send. That's expected if "
                "BREVO_API_KEY is empty."
            ))

        self.stdout.write(self.style.MIGRATE_HEADING(f"\n── Sending to {to_email} ──"))

        try:
            sent_count = send_mail(
                subject="BookMyStay — test email",
                message=(
                    "This is a diagnostic test email from BookMyStay.\n\n"
                    "If you're reading this in your inbox, the Brevo pipeline is working end-to-end."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                fail_silently=False,
            )
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"\n✘ Send failed: {type(exc).__name__}: {exc}"))
            self._print_hint(exc)
            raise CommandError("Email send failed — see diagnosis above.")

        if sent_count:
            self.stdout.write(self.style.SUCCESS(f"\n✔ send_mail() reported success (sent_count={sent_count})."))
            if 'anymail' in settings.EMAIL_BACKEND:
                self.stdout.write("Check the inbox (and spam folder) for " + to_email + ".")
            else:
                self.stdout.write("This was printed above, not actually delivered (console backend).")
        else:
            self.stdout.write(self.style.WARNING(
                "\nsend_mail() returned 0 — Django accepted the call but didn't report a message as sent. "
                "This can happen silently with fail_silently=True elsewhere in the app; worth checking "
                "Brevo's dashboard (Transactional → Logs) for the actual delivery status."
            ))

    def _print_hint(self, exc):
        """Best-effort plain-English hint based on common Anymail/Brevo failure modes."""
        msg = str(exc).lower()
        if 'unauthorized' in msg or '401' in msg or 'invalid api key' in msg:
            hint = "Your BREVO_API_KEY looks invalid or was rejected. Double check it in Brevo → SMTP & API → API Keys."
        elif 'sender' in msg and ('not' in msg or 'valid' in msg or 'verify' in msg):
            hint = (
                f"Brevo likely rejected the sender address ({settings.DEFAULT_FROM_EMAIL}). "
                "Make sure it's added and marked Verified under Brevo → Senders & IP."
            )
        elif 'connection' in msg or 'timeout' in msg or 'network' in msg:
            hint = "Couldn't reach Brevo's API — check the server's outbound network access to api.brevo.com."
        else:
            hint = "No specific pattern matched — read the raw error above for the exact reason."
        self.stdout.write(self.style.WARNING(f"Hint: {hint}"))
