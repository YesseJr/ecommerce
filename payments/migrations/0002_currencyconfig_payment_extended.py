# Migration: Add CurrencyConfig model + extend Payment with multi-currency & gateway fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [

        # ── 1. Create CurrencyConfig ──────────────────────────────────────────
        migrations.CreateModel(
            name='CurrencyConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usd_to_tzs', models.DecimalField(
                    decimal_places=2, default=2600.0, max_digits=10,
                    help_text='Exchange rate: 1 USD = this many TZS'
                )),
                ('usd_enabled', models.BooleanField(default=True, help_text='Allow payments in USD')),
                ('tzs_enabled', models.BooleanField(default=True, help_text='Allow payments in TZS (Tanzanian Shilling)')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Currency Configuration',
                'verbose_name_plural': 'Currency Configuration',
            },
        ),

        # ── 2. Rename Payment.method → payment_method ────────────────────────
        migrations.RenameField(
            model_name='payment',
            old_name='method',
            new_name='payment_method',
        ),

        # ── 3. Rename Payment.paid_at → payment_date ─────────────────────────
        migrations.RenameField(
            model_name='payment',
            old_name='paid_at',
            new_name='payment_date',
        ),

        # ── 4. Update payment_method choices (expanded) ───────────────────────
        migrations.AlterField(
            model_name='payment',
            name='payment_method',
            field=models.CharField(
                choices=[
                    ('credit_card', 'Credit Card'),
                    ('debit_card', 'Debit Card'),
                    ('mpesa', 'M-Pesa'),
                    ('airtel', 'Airtel Money'),
                    ('tigo', 'Tigo Pesa'),
                    ('halopesa', 'HaloPesa'),
                    ('card', 'Card (Legacy)'),
                    ('cash', 'Cash on Arrival'),
                    ('mix', 'Mixed Payment'),
                ],
                default='mpesa',
                max_length=20,
            ),
        ),

        # ── 5. Update status choices (add processing) ─────────────────────────
        migrations.AlterField(
            model_name='payment',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('processing', 'Processing'),
                    ('success', 'Successful'),
                    ('failed', 'Failed'),
                    ('refunded', 'Refunded'),
                ],
                default='pending', max_length=20,
            ),
        ),

        # ── 6. Resize amount field to support large TZS amounts ───────────────
        migrations.AlterField(
            model_name='payment',
            name='amount',
            field=models.DecimalField(
                decimal_places=2, max_digits=12,
                help_text='Charged amount in the selected currency'
            ),
        ),

        # ── 7. Add new Payment fields ─────────────────────────────────────────
        migrations.AddField(
            model_name='payment',
            name='provider',
            field=models.CharField(
                blank=True, max_length=50,
                help_text='Mobile money provider or card network'
            ),
        ),
        migrations.AddField(
            model_name='payment',
            name='currency',
            field=models.CharField(
                choices=[('USD', 'US Dollar (USD)'), ('TZS', 'Tanzanian Shilling (TZS)')],
                default='USD', max_length=3,
            ),
        ),
        migrations.AddField(
            model_name='payment',
            name='exchange_rate',
            field=models.DecimalField(
                decimal_places=2, default=1.0, max_digits=10,
                help_text='Exchange rate applied at payment time'
            ),
        ),
        migrations.AddField(
            model_name='payment',
            name='amount_usd',
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=10,
                help_text='Equivalent amount in USD'
            ),
        ),
        migrations.AddField(
            model_name='payment',
            name='authorization_code',
            field=models.CharField(blank=True, max_length=50,
                                   help_text='Card authorization code'),
        ),
        migrations.AddField(
            model_name='payment',
            name='receipt_number',
            field=models.CharField(blank=True, max_length=50,
                                   help_text='Mobile money receipt number'),
        ),
        migrations.AddField(
            model_name='payment',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
