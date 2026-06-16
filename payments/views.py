from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
import uuid
import random
import string
from bookings.models import Cart, Booking, BookingExtra
from .models import Payment


def generate_reference():
    """Generate unique booking reference like BMS-A3F9K2"""
    chars = string.ascii_uppercase + string.digits
    code  = ''.join(random.choices(chars, k=6))
    return f"BMS-{code}"


def generate_transaction_id():
    """Generate unique transaction ID"""
    return str(uuid.uuid4()).upper()[:16]


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

    return render(request, 'payments/checkout.html', {'cart': cart})


# ─── REPLACE process_payment() in payments/views.py ───
# Only the top section changes — add the availability re-check
# right after fetching the cart, before generating the reference.

@login_required
def process_payment(request):
    if not request.user.is_traveller:
        return redirect('properties:home')

    if request.method != 'POST':
        return redirect('payments:checkout')

    try:
        cart = Cart.objects.get(traveller=request.user)
    except Cart.DoesNotExist:
        messages.error(request, "Your cart is empty.")
        return redirect('properties:home')

    if not cart.booking_property or not cart.check_in or not cart.check_out:
        messages.error(request, "Please select a property and dates first.")
        return redirect('bookings:cart')

    # ✅ NEW: Final safety check — someone else may have booked
    # these exact dates while this traveller was at checkout.
    from properties.models import check_property_availability

    if not check_property_availability(cart.booking_property, cart.check_in, cart.check_out):
        messages.error(
            request,
            f"😔 Sorry, '{cart.booking_property.name}' was just booked for "
            f"those dates by someone else. Please choose different dates."
        )
        return redirect('properties:detail', slug=cart.booking_property.slug)

    payment_method = request.POST.get('payment_method', 'mpesa')

    # Simulate payment processing
    # In production this is where M-Pesa Daraja API call goes
    payment_success = True  # Always succeeds in our simulation

    if payment_success:
        reference = generate_reference()
        while Booking.objects.filter(reference=reference).exists():
            reference = generate_reference()

        # Create the Booking
        booking = Booking.objects.create(
            traveller       = request.user,
            booking_property = cart.booking_property,
            check_in        = cart.check_in,
            check_out       = cart.check_out,
            guests          = cart.guests,
            price_per_night = cart.booking_property.price_per_night,
            nights          = cart.nights,
            room_total      = cart.room_total,
            extras_total    = cart.extras_total,
            grand_total     = cart.grand_total,
            status          = 'confirmed',
            reference       = reference,
        )

        # Snapshot the extras into BookingExtra
        for item in cart.items.all():
            extra = item.extra

            if extra.charge_type == 'per_night':
                subtotal = extra.price * cart.nights
            elif extra.charge_type == 'per_person':
                subtotal = extra.price * cart.guests
            else:
                subtotal = extra.price

            BookingExtra.objects.create(
                booking    = booking,
                extra_name = extra.name,
                extra_price = extra.price,
                charge_type = extra.charge_type,
                subtotal   = subtotal,
            )

        # Create Payment record
        Payment.objects.create(
            booking        = booking,
            traveller      = request.user,
            amount         = cart.grand_total,
            method         = payment_method,
            status         = 'success',
            transaction_id = generate_transaction_id(),
            paid_at        = timezone.now(),
        )

        # Clear the cart after successful booking
        cart.items.all().delete()
        cart.booking_property = None
        cart.check_in         = None
        cart.check_out        = None
        cart.save()

        messages.success(
            request,
            f"Booking confirmed! Your reference is {reference} 🎉"
        )
        return redirect('payments:confirmation', reference=reference)

    else:
        messages.error(request, "Payment failed. Please try again.")
        return redirect('payments:checkout')


@login_required
def confirmation(request, reference):
    booking = get_object_or_404(
        Booking,
        reference=reference,
        traveller=request.user
    )
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
    ).order_by('-created_at')

    return render(request, 'payments/my_bookings.html', {
        'bookings': bookings,
    })