from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import date
from properties.models import Property, PropertyExtra, check_property_availability
from .models import Cart, CartItem


# ─── CART VIEWS ─────────────────────────────────────────

@login_required
def cart_view(request):
    if not request.user.is_traveller:
        messages.error(request, "Only travellers can access the cart.")
        return redirect('properties:home')

    try:
        cart = Cart.objects.get(traveller=request.user)
    except Cart.DoesNotExist:
        cart = None

    try:
        from payments.models import CurrencyConfig
        from payments.views import get_session_currency
        config   = CurrencyConfig.get_config()
        currency = get_session_currency(request)
        rate     = float(config.usd_to_tzs)
    except Exception:
        currency = 'USD'
        rate     = 2500.0

    return render(request, 'bookings/cart.html', {
        'cart':     cart,
        'currency': currency,
        'rate':     rate,
    })


@login_required
def add_to_cart(request, slug):
    if not request.user.is_traveller:
        messages.error(request, "Only travellers can book properties.")
        return redirect('properties:detail', slug=slug)

    prop = get_object_or_404(Property, slug=slug, status='active')

    if request.method == 'POST':
        check_in_str  = request.POST.get('check_in')
        check_out_str = request.POST.get('check_out')
        guests        = request.POST.get('guests', 1)

        # Validate dates
        try:
            check_in  = date.fromisoformat(check_in_str)
            check_out = date.fromisoformat(check_out_str)
        except (ValueError, TypeError):
            messages.error(request, "Please select valid dates.")
            return redirect('properties:detail', slug=slug)

        if check_in >= check_out:
            messages.error(request, "Check-out must be after check-in.")
            return redirect('properties:detail', slug=slug)

        if check_in < date.today():
            messages.error(request, "Check-in date cannot be in the past.")
            return redirect('properties:detail', slug=slug)

        # ✅ NEW: Check the property isn't already booked for these dates
        if not check_property_availability(prop, check_in, check_out):
            messages.error(
                request,
                f"😔 '{prop.name}' is already booked for some or all of those "
                f"dates. Please choose a different date range."
            )
            return redirect('properties:detail', slug=slug)

        # Get or create cart — one cart per traveller
        cart, created = Cart.objects.get_or_create(
            traveller=request.user
        )

        # If switching to a different property clear old extras
        if cart.booking_property and cart.booking_property != prop:
            cart.items.all().delete()
            messages.info(request, "Your previous cart was cleared for the new property.")

        # Update cart
        cart.booking_property = prop
        cart.check_in  = check_in
        cart.check_out = check_out
        cart.guests    = int(guests)
        cart.save()

        messages.success(request, f"'{prop.name}' added to your cart! 🛒")
        return redirect('bookings:cart')

    return redirect('properties:detail', slug=slug)


@login_required
def add_extra_to_cart(request, extra_pk):
    if request.method == 'POST':
        extra = get_object_or_404(PropertyExtra, pk=extra_pk)

        try:
            cart = Cart.objects.get(traveller=request.user)
        except Cart.DoesNotExist:
            messages.error(request, "Your cart is empty.")
            return redirect('properties:home')

        if extra.property_id != cart.booking_property_id:
            messages.error(request, "This extra doesn't belong to your current property.")
            return redirect('bookings:cart')

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            extra=extra
        )

        if created:
            messages.success(request, f"'{extra.name}' added to cart! ✅")
        else:
            messages.info(request, f"'{extra.name}' is already in your cart.")

    return redirect('bookings:cart')


@login_required
def remove_extra_from_cart(request, extra_pk):
    if request.method == 'POST':
        extra = get_object_or_404(PropertyExtra, pk=extra_pk)

        try:
            cart = Cart.objects.get(traveller=request.user)
            item = CartItem.objects.get(cart=cart, extra=extra)
            item.delete()
            messages.success(request, f"'{extra.name}' removed from cart.")
        except (Cart.DoesNotExist, CartItem.DoesNotExist):
            messages.error(request, "Item not found in cart.")

    return redirect('bookings:cart')


@login_required
def clear_cart(request):
    if request.method == 'POST':
        try:
            cart = Cart.objects.get(traveller=request.user)
            cart.items.all().delete()
            cart.booking_property = None
            cart.check_in         = None
            cart.check_out        = None
            cart.save()
            messages.success(request, "Cart cleared.")
        except Cart.DoesNotExist:
            pass
    return redirect('bookings:cart')