import uuid
import random
import string
import json
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from bookings.models import Cart, Booking, BookingExtra
from .models import Payment, CurrencyConfig


# ─── Generator Helpers ────────────────────────────────────────────────────────

def generate_reference():
    chars = string.ascii_uppercase + string.digits
    code  = ''.join(random.choices(chars, k=6))
    return f"BMS-{code}"


def generate_transaction_id():
    ts  = timezone.now().strftime('%Y%m%d%H%M')
    uid = str(uuid.uuid4()).replace('-', '').upper()[:8]
    return f"TXN-{uid}-{ts}"


def generate_auth_code():
    """Card authorization code (simulated)."""
    return 'AUTH-' + ''.join(random.choices(string.digits, k=6))


def generate_receipt_number(provider=''):
    """Mobile money receipt number (simulated)."""
    prefix = {
        'mpesa':    'MP',
        'airtel':   'AM',
        'tigo':     'TP',
        'halopesa': 'HP',
    }.get(provider, 'MM')
    code = ''.join(random.choices(string.digits + string.ascii_uppercase, k=10))
    return f"RCP-{prefix}-{code}"


# ─── Currency Helpers ─────────────────────────────────────────────────────────

def get_session_currency(request):
    return request.session.get('currency', 'USD')


def convert_amount(usd_amount, currency, rate):
    """Convert a USD amount to the target currency."""
    if currency == 'TZS':
        return Decimal(str(usd_amount)) * Decimal(str(rate))
    return Decimal(str(usd_amount))


# ─── Views ────────────────────────────────────────────────────────────────────

@login_required
def set_currency(request):
    """AJAX endpoint: switch active currency for the session."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            currency = data.get('currency', 'USD')
        except (json.JSONDecodeError, AttributeError):
            currency = request.POST.get('currency', 'USD')

        if currency in ('USD', 'TZS'):
            request.session['currency'] = currency
            config   = CurrencyConfig.get_config()
            rate     = float(config.usd_to_tzs)
            return JsonResponse({'success': True, 'currency': currency, 'rate': rate})
    return JsonResponse({'success': False}, status=400)


def currency_info(request):
    """AJAX endpoint: return current exchange rate config. Works for all users including guests."""
    config   = CurrencyConfig.get_config()
    currency = get_session_currency(request)
    return JsonResponse({
        'currency':     currency,
        'rate':         float(config.usd_to_tzs),
        'usd_enabled':  config.usd_enabled,
        'tzs_enabled':  config.tzs_enabled,
    })


@login_required
def checkout(request):
    if not request.user.is_traveller:
        return redirect('properties:home')

    try:
        cart = Cart.objects.get(traveller=request.user)
    except Cart.DoesNotExist:
        messages.error(request, "Your cart is empty.")
        return redirect('properties:home')

    if not cart.booking_property or not cart.check_in or not cart.check_out:
        messages.error(request, "Please select a property and dates first.")
        return redirect('bookings:cart')

    config   = CurrencyConfig.get_config()
    currency = get_session_currency(request)
    rate     = config.usd_to_tzs

    # Pre-compute converted totals for the template
    grand_usd   = cart.grand_total
    grand_local = convert_amount(grand_usd, currency, rate)

    MOBILE_PROVIDERS = [
        ('mpesa',    'M-Pesa'),
        ('airtel',   'Airtel Money'),
        ('tigo',     'Tigo Pesa'),
        ('halopesa', 'HaloPesa'),
    ]

    context = {
        'cart':        cart,
        'currency':    currency,
        'rate':        rate,
        'grand_usd':   grand_usd,
        'grand_local': grand_local,
        'config':      config,
        'providers':   MOBILE_PROVIDERS,
    }
    return render(request, 'payments/checkout.html', context)


@login_required
@require_POST
def process_payment(request):
    """
    AJAX-friendly endpoint that:
    1. Validates the cart
    2. Checks availability
    3. Creates Booking + BookingExtras + Payment
    4. Clears the cart
    5. Returns JSON { success, redirect_url } or { success, error }
    """
    if not request.user.is_traveller:
        return JsonResponse({'success': False, 'error': 'Not authorised.'}, status=403)

    # ── Fetch cart ────────────────────────────────────────────────────────────
    try:
        cart = Cart.objects.get(traveller=request.user)
    except Cart.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Your cart is empty.'})

    if not cart.booking_property or not cart.check_in or not cart.check_out:
        return JsonResponse({'success': False, 'error': 'Incomplete booking details.'})

    # ── Availability double-check ─────────────────────────────────────────────
    from properties.models import check_property_availability
    if not check_property_availability(cart.booking_property, cart.check_in, cart.check_out):
        return JsonResponse({
            'success': False,
            'error': (
                f"'{cart.booking_property.name}' was just booked for those dates "
                "by someone else. Please choose different dates."
            )
        })

    # ── Parse posted payment data ─────────────────────────────────────────────
    payment_method = request.POST.get('payment_method', 'mpesa')
    provider       = request.POST.get('provider', '')
    currency       = request.POST.get('currency', 'USD')
    if currency not in ('USD', 'TZS'):
        currency = 'USD'

    config        = CurrencyConfig.get_config()
    rate          = config.usd_to_tzs
    grand_usd     = cart.grand_total
    amount_local  = convert_amount(grand_usd, currency, rate)
    exchange_rate = rate if currency == 'TZS' else Decimal('1.00')

    # ── Generate unique booking reference ─────────────────────────────────────
    reference = generate_reference()
    while Booking.objects.filter(reference=reference).exists():
        reference = generate_reference()

    # ── Create Booking ────────────────────────────────────────────────────────
    booking = Booking.objects.create(
        traveller        = request.user,
        booking_property = cart.booking_property,
        check_in         = cart.check_in,
        check_out        = cart.check_out,
        guests           = cart.guests,
        price_per_night  = cart.booking_property.price_per_night,
        nights           = cart.nights,
        room_total       = cart.room_total,
        extras_total     = cart.extras_total,
        grand_total      = cart.grand_total,
        status           = 'confirmed',
        reference        = reference,
    )

    # ── Snapshot extras ───────────────────────────────────────────────────────
    for item in cart.items.all():
        extra = item.extra
        if extra.charge_type == 'per_night':
            subtotal = extra.price * cart.nights
        elif extra.charge_type == 'per_person':
            subtotal = extra.price * cart.guests
        else:
            subtotal = extra.price

        BookingExtra.objects.create(
            booking     = booking,
            extra_name  = extra.name,
            extra_price = extra.price,
            charge_type = extra.charge_type,
            subtotal    = subtotal,
        )

    # ── Build payment record ──────────────────────────────────────────────────
    txn_id   = generate_transaction_id()
    auth_code   = ''
    receipt_num = ''

    if payment_method in ('credit_card', 'debit_card', 'card'):
        auth_code = generate_auth_code()
        provider  = provider or ('Visa' if payment_method == 'credit_card' else 'Mastercard')
    else:
        receipt_num = generate_receipt_number(payment_method)
        # provider comes from POST (mpesa, airtel, tigo, halopesa)
        if not provider:
            provider = payment_method

    Payment.objects.create(
        booking            = booking,
        traveller          = request.user,
        payment_method     = payment_method,
        provider           = provider,
        currency           = currency,
        exchange_rate      = exchange_rate,
        amount             = amount_local,
        amount_usd         = grand_usd,
        transaction_id     = txn_id,
        authorization_code = auth_code,
        receipt_number     = receipt_num,
        status             = 'success',
        payment_date       = timezone.now(),
    )

    # ── Clear cart ────────────────────────────────────────────────────────────
    cart.items.all().delete()
    cart.booking_property = None
    cart.check_in         = None
    cart.check_out        = None
    cart.save()

    # ── Update session currency ───────────────────────────────────────────────
    request.session['currency'] = currency

    from django.urls import reverse
    redirect_url = reverse('payments:confirmation', args=[reference])

    return JsonResponse({
        'success':        True,
        'redirect_url':   redirect_url,
        'reference':      reference,
        'transaction_id': txn_id,
    })


@login_required
def confirmation(request, reference):
    booking = get_object_or_404(Booking, reference=reference, traveller=request.user)
    payment = get_object_or_404(Payment, booking=booking)
    return render(request, 'payments/confirmation.html', {
        'booking': booking,
        'payment': payment,
    })


@login_required
def my_bookings(request):
    if not request.user.is_traveller:
        return redirect('properties:home')

    bookings = Booking.objects.filter(
        traveller=request.user
    ).select_related('booking_property').prefetch_related('payment').order_by('-created_at')

    currency = get_session_currency(request)
    try:
        config = CurrencyConfig.get_config()
        rate   = float(config.usd_to_tzs)
    except Exception:
        rate = 2500.0

    return render(request, 'payments/my_bookings.html', {
        'bookings': bookings,
        'currency': currency,
        'rate':     rate,
    })


@login_required
def payment_history(request):
    """Show full payment history for the logged-in traveller."""
    if not request.user.is_traveller:
        return redirect('properties:home')

    payments = Payment.objects.filter(
        traveller=request.user
    ).select_related('booking', 'booking__booking_property').order_by('-created_at')

    # Optional filters from GET params
    status_filter = request.GET.get('status', '')
    method_filter = request.GET.get('method', '')

    if status_filter:
        payments = payments.filter(status=status_filter)
    if method_filter:
        payments = payments.filter(payment_method=method_filter)

    return render(request, 'payments/payment_history.html', {
        'payments':       payments,
        'status_filter':  status_filter,
        'method_filter':  method_filter,
        'status_choices': Payment.STATUS_CHOICES,
        'method_choices': Payment.METHOD_CHOICES[:6],  # exclude legacy
    })
