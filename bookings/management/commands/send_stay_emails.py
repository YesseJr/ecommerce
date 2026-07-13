"""
Sends the day-of-stay emails: a "welcome" note to guests whose check-in is
today, and a "goodbye" note to guests whose check-out is today.

Meant to run once per day via cron (Linux/macOS) or Task Scheduler
(Windows) — see the docstring at the bottom for setup examples.

If your hosting doesn't give you shell/cron access, use the HTTP fallback
at /bookings/cron/send-stay-emails/<CRON_SECRET>/ with a free external
cron service instead (e.g. cron-job.org). See bookings/views.py.

Usage:
    python manage.py send_stay_emails
    python manage.py send_stay_emails --dry-run
"""
from datetime import date

from django.core.management.base import BaseCommand

from bookings.models import Booking
from bookings.emails import run_daily_stay_email_sweep


class Command(BaseCommand):
    help = "Sends welcome emails (check-in today) and goodbye emails (check-out today)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help="List what would be sent without actually sending anything."
        )

    def handle(self, *args, **options):
        today = date.today()

        if options['dry_run']:
            checking_in = Booking.objects.filter(
                status='confirmed', check_in=today, welcome_email_sent=False
            ).select_related('traveller', 'booking_property')
            checking_out = Booking.objects.filter(
                status='confirmed', check_out=today, goodbye_email_sent=False
            ).select_related('traveller', 'booking_property')

            self.stdout.write(f"Today: {today}")
            self.stdout.write(f"Check-ins to welcome:  {checking_in.count()}")
            self.stdout.write(f"Check-outs to thank:   {checking_out.count()}")
            for b in checking_in:
                self.stdout.write(f"  [welcome] {b.reference} — {b.traveller.email} @ {b.booking_property.name}")
            for b in checking_out:
                self.stdout.write(f"  [goodbye] {b.reference} — {b.traveller.email} @ {b.booking_property.name}")
            self.stdout.write(self.style.WARNING("Dry run — nothing sent."))
            return

        result = run_daily_stay_email_sweep()
        self.stdout.write(self.style.SUCCESS(
            f"Sent {result['welcome_sent']} welcome email(s) and {result['goodbye_sent']} goodbye email(s)."
        ))


# ── Scheduling this command ────────────────────────────────────────────────
#
# Linux/macOS (cron) — run once a day at 8 AM:
#     0 8 * * * cd /path/to/project && /path/to/venv/bin/python manage.py send_stay_emails
#
# Windows (Task Scheduler):
#     Program/script:  C:\path\to\venv\Scripts\python.exe
#     Arguments:        manage.py send_stay_emails
#     Start in:         C:\path\to\project
#     Trigger:           Daily, e.g. 8:00 AM
