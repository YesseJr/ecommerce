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
from .models import Payment, CurrencyConfig, Coupon


# ─── Coupon session key helper ─────────────────────────────────────────────

def _coupon_session_key(user):
    return f'coupon_code_{user.id}'


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

    # Coupon (if applied earlier via AJAX and stored in session)
    coupon = None
    discount_usd = Decimal('0')
    coupon_code = request.session.get(_coupon_session_key(request.user))
    if coupon_code:
        coupon = Coupon.objects.filter(code__iexact=coupon_code).first()
        if coupon:
            valid, _msg = coupon.is_valid(amount=cart.grand_total)
            if valid:
                discount_usd = Decimal(str(coupon.calculate_discount(cart.grand_total)))
            else:
                coupon = None
                request.session.pop(_coupon_session_key(request.user), None)

    # Pre-compute converted totals for the template
    grand_usd   = cart.total_with_fees(discount=discount_usd)
    grand_local = convert_amount(grand_usd, currency, rate)

    MOBILE_PROVIDERS = [
        ('mpesa',    'M-Pesa'),
        ('airtel',   'Airtel Money'),
        ('tigo',     'Tigo Pesa'),
        ('halopesa', 'HaloPesa'),
    ]

    context = {
        'cart':          cart,
        'currency':      currency,
        'rate':          rate,
        'grand_usd':     grand_usd,
        'grand_local':   grand_local,
        'service_fee':   cart.service_fee,
        'tax_amount':    cart.tax_amount,
        'coupon':        coupon,
        'discount_usd':  discount_usd,
        'config':        config,
        'providers':     MOBILE_PROVIDERS,
    }
    return render(request, 'payments/checkout.html', context)


@login_required
@require_POST
def apply_coupon(request):
    """AJAX endpoint — validates a coupon code against the current cart."""
    code = request.POST.get('code', '').strip()
    if not code:
        return JsonResponse({'success': False, 'error': 'Enter a coupon code.'})

    try:
        cart = Cart.objects.get(traveller=request.user)
    except Cart.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Your cart is empty.'})

    coupon = Coupon.objects.filter(code__iexact=code).first()
    if not coupon:
        return JsonResponse({'success': False, 'error': 'That coupon code was not found.'})

    valid, msg = coupon.is_valid(amount=cart.grand_total)
    if not valid:
        return JsonResponse({'success': False, 'error': msg})

    request.session[_coupon_session_key(request.user)] = coupon.code
    discount = coupon.calculate_discount(cart.grand_total)
    new_total = cart.total_with_fees(discount=Decimal(str(discount)))

    return JsonResponse({
        'success': True,
        'code': coupon.code,
        'discount': float(discount),
        'new_total': float(new_total),
    })


@login_required
@require_POST
def remove_coupon(request):
    request.session.pop(_coupon_session_key(request.user), None)
    return JsonResponse({'success': True})


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

    # ── Coupon (validated earlier via AJAX, stored in session) ────────────────
    coupon = None
    discount_usd = Decimal('0')
    coupon_code = request.session.get(_coupon_session_key(request.user))
    if coupon_code:
        coupon = Coupon.objects.filter(code__iexact=coupon_code).first()
        if coupon:
            valid, _msg = coupon.is_valid(amount=cart.grand_total)
            if valid:
                discount_usd = Decimal(str(coupon.calculate_discount(cart.grand_total)))
            else:
                coupon = None

    service_fee = cart.service_fee
    tax_amount  = cart.tax_amount
    grand_usd     = cart.total_with_fees(discount=discount_usd)
    amount_local  = convert_amount(grand_usd, currency, rate)
    exchange_rate = rate if currency == 'TZS' else Decimal('1.00')

    # ── Generate unique booking reference ─────────────────────────────────────
    reference = generate_reference()
    while Booking.objects.filter(reference=reference).exists():
        reference = generate_reference()

    children = cart.children or 0
    adults   = max(cart.guests - children, 1)

    # ── Create Booking ────────────────────────────────────────────────────────
    booking = Booking.objects.create(
        traveller        = request.user,
        booking_property = cart.booking_property,
        check_in         = cart.check_in,
        check_out        = cart.check_out,
        guests           = cart.guests,
        adults           = adults,
        children         = children,
        special_requests = cart.special_requests,
        price_per_night  = cart.booking_property.price_per_night,
        nights           = cart.nights,
        room_total       = cart.room_total,
        extras_total     = cart.extras_total,
        tax_amount       = tax_amount,
        service_fee      = service_fee,
        discount_amount  = discount_usd,
        grand_total      = grand_usd,
        coupon           = coupon,
        cancellation_policy = cart.booking_property.cancellation_policy,
        status           = 'confirmed',
        reference        = reference,
    )

    if coupon:
        Coupon.objects.filter(pk=coupon.pk).update(used_count=coupon.used_count + 1)
        request.session.pop(_coupon_session_key(request.user), None)

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


@login_required
def cancel_booking(request, reference):
    """Guest-initiated cancellation, refund computed from the snapshotted
    cancellation policy on the booking (not the live property setting)."""
    booking = get_object_or_404(Booking, reference=reference, traveller=request.user)

    if not booking.is_cancellable:
        messages.error(request, "This booking can no longer be cancelled.")
        return redirect('payments:my_bookings')

    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        refund = booking.calculate_refund()

        booking.status = 'cancelled'
        booking.cancelled_at = timezone.now()
        booking.cancellation_reason = reason
        booking.refund_amount = refund
        booking.save()

        try:
            payment = booking.payment
            payment.status = 'refunded' if refund > 0 else 'cancelled'
            payment.save()
        except Payment.DoesNotExist:
            pass

        from inbox.models import Notification
        Notification.send(
            booking.booking_property.owner,
            title=f"Booking cancelled: {booking.booking_property.name}",
            body=f"{request.user.first_name or request.user.username} cancelled their stay ({booking.reference}).",
            link=f'/dashboard/bookings/',
            notif_type='booking',
        )

        if refund > 0:
            messages.success(request, f"Booking cancelled. ${refund:.2f} will be refunded per the {booking.get_cancellation_policy_display() if booking.cancellation_policy else 'cancellation'} policy.")
        else:
            messages.warning(request, "Booking cancelled. This booking wasn't eligible for a refund under its cancellation policy.")

        return redirect('payments:my_bookings')

    return render(request, 'payments/cancel_booking.html', {
        'booking': booking,
        'estimated_refund': booking.calculate_refund(),
    })
