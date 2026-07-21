from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
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

    # One-time upsell suggestion — popped so it only shows once, right
    # after the add that triggered it, not on every future cart visit.
    suggested_extra = None
    suggestion_id = request.session.pop('extra_suggestion_id', None)
    if suggestion_id and cart:
        suggested_extra = PropertyExtra.objects.filter(
            pk=suggestion_id, is_available=True
        ).exclude(
            pk__in=cart.items.values_list('extra_id', flat=True)
        ).first()

    return render(request, 'bookings/cart.html', {
        'cart':             cart,
        'currency':         currency,
        'rate':             rate,
        'suggested_extra':  suggested_extra,
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
        children      = request.POST.get('children', 0)
        special_requests = request.POST.get('special_requests', '').strip()

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
        try:
            cart.children = max(int(children), 0)
        except (TypeError, ValueError):
            cart.children = 0
        cart.special_requests = special_requests
        cart.save()

        messages.success(request, f"'{prop.name}' added to your cart! 🛒")
        return redirect('bookings:cart')

    return redirect('properties:detail', slug=slug)


@login_required
def sync_cart_extras(request):
    """
    One submit, any number of extras — checked boxes get added, unchecked
    ones already in the cart get removed, in a single request instead of
    a page reload per extra.
    """
    if request.method != 'POST':
        return redirect('bookings:cart')

    try:
        cart = Cart.objects.get(traveller=request.user)
    except Cart.DoesNotExist:
        messages.error(request, "Your cart is empty.")
        return redirect('properties:home')

    if not cart.booking_property:
        messages.error(request, "Add a property to your cart first.")
        return redirect('bookings:cart')

    submitted_ids = {
        int(i) for i in request.POST.getlist('extra_ids') if i.isdigit()
    }
    # Safety: only ever act on extras this property actually offers —
    # ignore anything submitted that doesn't belong here.
    valid_ids = set(
        cart.booking_property.extras.filter(is_available=True).values_list('pk', flat=True)
    )
    selected_ids = submitted_ids & valid_ids

    current_ids = set(cart.items.values_list('extra_id', flat=True))
    to_add = selected_ids - current_ids
    to_remove = current_ids - selected_ids

    if to_add:
        CartItem.objects.bulk_create([CartItem(cart=cart, extra_id=eid) for eid in to_add])
    if to_remove:
        cart.items.filter(extra_id__in=to_remove).delete()

    if to_add or to_remove:
        parts = []
        if to_add:
            parts.append(f"{len(to_add)} extra{'s' if len(to_add) != 1 else ''} added")
        if to_remove:
            parts.append(f"{len(to_remove)} removed")
        messages.success(request, f"{' · '.join(parts)}. ✅")
    else:
        messages.info(request, "No changes to your extras.")

    # ── Upsell nudge — only fires when something was actually just added,
    # and only suggests an extra they genuinely haven't picked yet. ──────
    if to_add:
        remaining = cart.booking_property.extras.filter(is_available=True).exclude(
            pk__in=selected_ids
        )
        if remaining.exists():
            food_pick = remaining.filter(
                Q(name__icontains='breakfast') | Q(name__icontains='meal') |
                Q(name__icontains='dinner') | Q(name__icontains='food')
            ).first()
            request.session['extra_suggestion_id'] = (food_pick or remaining.first()).pk

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

@login_required
def update_cart_notes(request):
    """Save/update the special-requests note on the traveller's cart."""
    if request.method == 'POST':
        try:
            cart = Cart.objects.get(traveller=request.user)
            cart.special_requests = request.POST.get('special_requests', '').strip()
            cart.save()
            messages.success(request, "Note saved.")
        except Cart.DoesNotExist:
            pass
    return redirect('bookings:cart')


# ─── CRON FALLBACK (for hosts without shell/cron access) ─────────────────

from django.conf import settings
from django.http import JsonResponse, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET


@csrf_exempt
@require_GET
def cron_send_stay_emails(request, secret):
    """
    Secured HTTP trigger for the same daily email sweep the management
    command runs — for hosting environments with no cron/Task Scheduler
    access. Point a free external scheduler (e.g. cron-job.org, or a
    GitHub Actions scheduled workflow) at this URL once a day.

    Disabled entirely (404) unless CRON_SECRET is set in the environment,
    and only responds if the secret in the URL matches exactly — this is
    a plain shared-secret check, not a full auth system, but it's enough
    to stop randos from triggering it or discovering it exists.
    """
    if not settings.CRON_SECRET:
        return HttpResponseNotFound()
    if secret != settings.CRON_SECRET:
        return HttpResponseNotFound()

    from .emails import run_daily_stay_email_sweep
    result = run_daily_stay_email_sweep()
    return JsonResponse({'ok': True, **result})
