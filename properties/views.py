from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.text import slugify
from django.db.models import Q, Sum

import properties
from .models import Property, PropertyImage, PropertyExtra, Amenity
from .forms import PropertyForm, PropertyExtraForm
from datetime import date
from django.http import Http404
import json
import calendar
from django.utils import timezone

# Currency helpers — imported lazily to avoid circular import
def _get_currency_context(request):
    """Return currency and rate for template context."""
    try:
        from payments.models import CurrencyConfig
        from payments.views import get_session_currency
        config   = CurrencyConfig.get_config()
        currency = get_session_currency(request)
        rate     = float(config.usd_to_tzs)
    except Exception:
        currency = 'USD'
        rate     = 2500.0
    return currency, rate

# ─── PUBLIC VIEWS ───────────────────────────────────────


def home(request):
    from django.db.models import Avg
    from reviews.models import Review
    from bookings.models import Booking
    from users.models import User

    featured = Property.objects.filter(
        status='active',
        is_available=True
    ).order_by('-is_featured', '-created_at')[:6]

    # ── Real DB stats for the homepage strip ──────────────────────────────────
    total_properties = Property.objects.filter(status='active').count()
    total_cities     = Property.objects.filter(status='active').values('city').distinct().count()
    total_guests     = Booking.objects.filter(status='confirmed').count()

    # Average rating across all reviews (round to 1dp)
    avg_rating_result = Review.objects.filter(is_hidden=False).aggregate(avg=Avg('rating'))['avg']
    avg_rating        = round(avg_rating_result, 1) if avg_rating_result else None

    cities = Property.objects.filter(
        status='active'
    ).values_list('city', flat=True).distinct()

    # ── Hero slider images — pulled from real, verified listings ──────────
    # Grabs one photo per property (first uploaded image) across the most
    # recent active listings, so the hero always reflects real inventory.
    # Each slide also carries a gradient so if the photo URL 404s (e.g. no
    # media/ uploaded yet on a fresh deploy) the hero still looks intentional.
    HERO_GRADIENTS = [
        'linear-gradient(135deg, #F97316 0%, #C2410C 45%, #1B3A6B 100%)',
        'linear-gradient(135deg, #0F766E 0%, #164E63 55%, #0F2347 100%)',
        'linear-gradient(135deg, #1B3A6B 0%, #312E81 55%, #111118 100%)',
        'linear-gradient(135deg, #D97706 0%, #7C2D12 55%, #111118 100%)',
        'linear-gradient(135deg, #0891B2 0%, #1B3A6B 55%, #111118 100%)',
    ]
    hero_images = []
    for prop in featured:
        img = prop.images.first()
        if img:
            hero_images.append({
                'url': img.image.url,
                'name': prop.name,
                'city': prop.city,
                'gradient': HERO_GRADIENTS[len(hero_images) % len(HERO_GRADIENTS)],
            })
        if len(hero_images) >= 5:
            break

    # ── Testimonials — top-rated real guest reviews ───────────────────────
    testimonials = Review.objects.select_related('traveller', 'property') \
        .filter(rating__gte=4, is_hidden=False) \
        .order_by('-rating', '-created_at')[:6]

    # ── Explore-by-area gallery — one representative photo + live count
    # per neighborhood, built from real listings (no hardcoded destinations).
    # Falls back to city name if a property hasn't set a neighborhood yet. ─
    city_gallery = []
    seen_areas = set()
    for prop in Property.objects.filter(status='active').select_related().order_by('-created_at'):
        area = prop.neighborhood or prop.city
        if area in seen_areas:
            continue
        img = prop.images.first()
        if not img:
            continue
        seen_areas.add(area)
        city_gallery.append({
            'city':  area,
            'url':   img.image.url,
            'count': Property.objects.filter(status='active').filter(
                        Q(neighborhood=area) | Q(neighborhood='', city=area)
                     ).count(),
            'gradient': HERO_GRADIENTS[len(city_gallery) % len(HERO_GRADIENTS)],
        })
        if len(city_gallery) >= 5:
            break

    currency, rate = _get_currency_context(request)
    return render(request, 'properties/home.html', {
        'featured':          featured,
        'cities':            cities,
        'property_types':    Property.PROPERTY_TYPES,
        'currency':          currency,
        'rate':              rate,
        # Real stats
        'total_properties':  total_properties,
        'total_cities':      total_cities,
        'total_guests':      total_guests,
        'avg_rating':        avg_rating,
        # Hero + social proof
        'hero_images':       hero_images,
        'testimonials':      testimonials,
        'city_gallery':      city_gallery,
    })

def property_list(request):
    properties = Property.objects.filter(
        status='active',
        is_available=True
    )

    # Search & Filter
    query      = request.GET.get('q', '')
    city       = request.GET.get('city', '')
    prop_type  = request.GET.get('type', '')
    min_price  = request.GET.get('min_price', '')
    max_price  = request.GET.get('max_price', '')
    guests     = request.GET.get('guests', '')
    check_in   = request.GET.get('check_in', '')
    check_out  = request.GET.get('check_out', '')
    amenity_ids = request.GET.getlist('amenities')
    sort       = request.GET.get('sort', 'newest')

    if query:
        properties = properties.filter(
            Q(name__icontains=query) |
            Q(city__icontains=query) |
            Q(neighborhood__icontains=query) |
            Q(description__icontains=query)
        )
    if city:
        properties = properties.filter(city__icontains=city)
    if prop_type:
        properties = properties.filter(property_type=prop_type)
    if min_price:
        properties = properties.filter(price_per_night__gte=min_price)
    if max_price:
        properties = properties.filter(price_per_night__lte=max_price)
    if guests:
        properties = properties.filter(max_guests__gte=guests)

    # Amenities: property must have ALL selected amenities
    if amenity_ids:
        for aid in amenity_ids:
            properties = properties.filter(amenities__amenity_id=aid)
        properties = properties.distinct()

    # Availability: exclude properties with a confirmed overlapping booking
    if check_in and check_out:
        try:
            from datetime import datetime as _dt
            from bookings.models import Booking
            ci = _dt.strptime(check_in, '%Y-%m-%d').date()
            co = _dt.strptime(check_out, '%Y-%m-%d').date()
            if co > ci:
                busy_property_ids = Booking.objects.filter(
                    status__in=['confirmed', 'pending'],
                    check_in__lt=co,
                    check_out__gt=ci,
                ).values_list('booking_property_id', flat=True)
                properties = properties.exclude(id__in=busy_property_ids)
        except ValueError:
            pass

    SORT_MAP = {
        'newest':     '-created_at',
        'price_low':  'price_per_night',
        'price_high': '-price_per_night',
    }
    if sort == 'rating':
        from django.db.models import Avg
        properties = properties.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating', '-created_at')
    else:
        properties = properties.order_by(SORT_MAP.get(sort, '-created_at'))

    cities = Property.objects.filter(
        status='active'
    ).values_list('city', flat=True).distinct()

    from .models import Amenity
    all_amenities = Amenity.objects.all()

    wishlisted_ids = set()
    if request.user.is_authenticated:
        from .models import Wishlist
        wishlisted_ids = set(Wishlist.objects.filter(user=request.user).values_list('property_id', flat=True))

    currency, rate = _get_currency_context(request)
    return render(request, 'properties/list.html', {
        'properties':     properties,
        'cities':         cities,
        'property_types': Property.PROPERTY_TYPES,
        'all_amenities':  all_amenities,
        'wishlisted_ids': wishlisted_ids,
        'currency':       currency,
        'rate':           rate,
        'filters': {
            'q': query, 'city': city,
            'type': prop_type, 'min_price': min_price,
            'max_price': max_price, 'guests': guests,
            'check_in': check_in, 'check_out': check_out,
            'amenities': [int(a) for a in amenity_ids if a.isdigit()],
            'sort': sort,
        }
    })


# ─── REPLACE the existing property_detail() view in properties/views.py ───

# ─── UPDATE property_detail() in properties/views.py ───
# Add unavailable_dates to the context so the template can
# pass them to JavaScript for date-picker validation.

def property_detail(request, slug):
    prop = Property.objects.filter(slug=slug, status='active').first()

    if not prop:
        if request.user.is_authenticated:
            prop = get_object_or_404(
                Property,
                slug=slug,
                owner=request.user
            )
        else:
            raise Http404("Property not found.")

    extras  = prop.extras.filter(is_available=True)
    images  = prop.images.all()
    reviews = prop.reviews.filter(is_hidden=False).order_by('-created_at')[:5]

    # Unavailable date ranges from confirmed/pending bookings
    import json
    from bookings.models import Booking

    bookings = Booking.objects.filter(
        booking_property=prop,
        status__in=['confirmed', 'pending']
    ).values('check_in', 'check_out')

    unavailable_dates = [
        {
            'check_in':  b['check_in'].strftime('%Y-%m-%d'),
            'check_out': b['check_out'].strftime('%Y-%m-%d'),
        }
        for b in bookings
    ]

    images_qs = prop.images.all()
    images_count = images_qs.count()

    # Track "recently viewed" for signed-in guests
    is_wishlisted = False
    if request.user.is_authenticated:
        from .models import RecentlyViewed, Wishlist
        if request.user != prop.owner:
            RecentlyViewed.objects.update_or_create(
                user=request.user, property=prop
            )
        is_wishlisted = Wishlist.objects.filter(user=request.user, property=prop).exists()

    from .models import get_similar_properties
    similar_properties = get_similar_properties(prop, limit=4)

    currency, rate = _get_currency_context(request)
    return render(request, 'properties/detail.html', {
        'property':               prop,
        'extras':                 extras,
        'images':                 images_qs,
        'images_count':           images_count,
        'reviews':                reviews,
        'today':                  date.today().isoformat(),
        'unavailable_dates_json': json.dumps(unavailable_dates),
        'guest_range':            range(1, prop.max_guests + 1),
        'rating_range':           range(1, 6),
        'currency':               currency,
        'rate':                   rate,
        'similar_properties':     similar_properties,
        'is_wishlisted':          is_wishlisted,
    })
# ─── OWNER VIEWS ────────────────────────────────────────


@login_required
def owner_dashboard(request):
    if not request.user.is_owner:
        messages.error(request, "Access denied. Owner accounts only.")
        return redirect('properties:home')

    properties = Property.objects.filter(
        owner=request.user
    ).order_by('-created_at')

    # Quick stats
    total      = properties.count()
    active     = properties.filter(status='active').count()
    pending    = properties.filter(status='pending').count()
    inactive = properties.filter(status='inactive').count()

    currency, rate = _get_currency_context(request)
    return render(request, 'properties/owner_dashboard.html', {
        'properties': properties,
        'total':      total,
        'active':     active,
        'pending':    pending,
        'inactive':   inactive,
        'currency':   currency,
        'rate':       rate,
    })


@login_required
def add_property(request):
    if not request.user.is_owner:
        messages.error(request, "Access denied. Owner accounts only.")
        return redirect('properties:home')

    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            prop = form.save(commit=False)
            prop.owner = request.user
            prop.slug = slugify(prop.name)

            # Ensure unique slug
            base_slug = prop.slug
            counter = 1
            while Property.objects.filter(slug=prop.slug).exists():
                prop.slug = f"{base_slug}-{counter}"
                counter += 1

            prop.save()

            # Handle multiple image uploads
            images = request.FILES.getlist('images')
            for i, image in enumerate(images):
                PropertyImage.objects.create(
                    property=prop,
                    image=image,
                    is_primary=(i == 0)
                )

            messages.success(
                request,
                "Property listed successfully! 🎉 It's under review."
            )
            return redirect('properties:owner_dashboard')
    else:
        form = PropertyForm()

    return render(request, 'properties/add_property.html', {'form': form})


@login_required
def edit_property(request, slug):
    prop = get_object_or_404(Property, slug=slug, owner=request.user)

    if request.method == 'POST':

        # ── Photo-only upload (comes from the separate "Add More Photos" form)
        # Detected by the absence of the 'name' field which the main form always sends
        if 'name' not in request.POST:
            images = request.FILES.getlist('images')
            for image in images:
                PropertyImage.objects.create(property=prop, image=image, is_primary=False)
            messages.success(request, "Photos uploaded successfully! 📸")
            return redirect('properties:edit_property', slug=prop.slug)

        # ── Main property edit form
        form = PropertyForm(request.POST, request.FILES, instance=prop)
        if form.is_valid():
            prop = form.save(commit=False)

            # FIX #1: Regenerate slug if name changed
            new_slug = slugify(prop.name)
            if new_slug != prop.slug:
                base_slug = new_slug
                counter = 1
                while Property.objects.filter(slug=new_slug).exclude(pk=prop.pk).exists():
                    new_slug = f"{base_slug}-{counter}"
                    counter += 1
                prop.slug = new_slug

            prop.save()
            messages.success(request, "Property updated successfully! ✅")
            return redirect('properties:edit_property', slug=prop.slug)

    else:
        form = PropertyForm(instance=prop)

    return render(request, 'properties/edit_property.html', {
        'form': form,
        'property': prop,
    })


@login_required
def delete_property(request, slug):
    prop = get_object_or_404(Property, slug=slug, owner=request.user)
    if request.method == 'POST':
        prop.delete()
        messages.success(request, "Property deleted.")
    return redirect('properties:owner_dashboard')


@login_required
def manage_extras(request, slug):
    prop = get_object_or_404(Property, slug=slug, owner=request.user)
    extras = prop.extras.all()

    if request.method == 'POST':
        form = PropertyExtraForm(request.POST)
        if form.is_valid():
            extra = form.save(commit=False)
            extra.property = prop
            extra.save()
            messages.success(request, f"'{extra.name}' added as an extra! ✅")
            return redirect('properties:manage_extras', slug=slug)
    else:
        form = PropertyExtraForm()

    currency, rate = _get_currency_context(request)
    return render(request, 'properties/manage_extras.html', {
        'property': prop,
        'extras':   extras,
        'form':     form,
        'currency': currency,
        'rate':     rate,
    })


@login_required
def delete_extra(request, pk):
    extra = get_object_or_404(PropertyExtra, pk=pk, property__owner=request.user)
    slug = extra.property.slug
    extra.delete()
    messages.success(request, "Extra removed.")
    return redirect('properties:manage_extras', slug=slug)

# ─── ADD THESE TWO NEW VIEWS to properties/views.py ─────
# Place them right after delete_extra() and before owner_bookings()

@login_required
def delete_image(request, pk):
    """Owner deletes one of their property images."""
    image = get_object_or_404(
        PropertyImage,
        pk=pk,
        property__owner=request.user
    )
    slug = image.property.slug
    was_primary = image.is_primary

    if request.method == 'POST':
        image.delete()

        # If we deleted the primary image, promote another one
        if was_primary:
            next_image = PropertyImage.objects.filter(
                property__slug=slug
            ).first()
            if next_image:
                next_image.is_primary = True
                next_image.save()

        messages.success(request, "Image removed.")

    return redirect('properties:edit_property', slug=slug)


@login_required
def set_primary_image(request, pk):
    """Owner sets a specific image as the primary/cover photo."""
    image = get_object_or_404(
        PropertyImage,
        pk=pk,
        property__owner=request.user
    )

    if request.method == 'POST':
        # Unset all other images as primary first
        PropertyImage.objects.filter(
            property=image.property
        ).update(is_primary=False)

        image.is_primary = True
        image.save()

        messages.success(request, "Cover photo updated! ✅")

    return redirect('properties:edit_property', slug=image.property.slug)

@login_required
def owner_bookings(request):
    if not request.user.is_owner:
        messages.error(request, "Access denied.")
        return redirect('properties:home')

    from bookings.models import Booking

    # Get all bookings for this owner's properties
    bookings = Booking.objects.filter(
        booking_property__owner=request.user
    ).order_by('-created_at')

    # Stats
    total     = bookings.count()
    confirmed = bookings.filter(status='confirmed').count()
    revenue   = sum(b.grand_total for b in bookings.filter(status='confirmed'))

    return render(request, 'properties/owner_bookings.html', {
        'bookings':  bookings,
        'total':     total,
        'confirmed': confirmed,
        'revenue':   revenue,
    })

@login_required
def owner_revenue(request):
    if not request.user.is_owner:
        messages.error(request, "Access denied.")
        return redirect('properties:home')

    from bookings.models import Booking

    properties = Property.objects.filter(owner=request.user)

    # Only CONFIRMED bookings count as real revenue
    confirmed_bookings = Booking.objects.filter(
        booking_property__owner=request.user,
        status='confirmed'
    )

    # ── Per-property breakdown ──────────────────────────
    property_stats = []
    for prop in properties:
        prop_bookings  = confirmed_bookings.filter(booking_property=prop)
        revenue        = prop_bookings.aggregate(total=Sum('grand_total'))['total'] or 0
        bookings_count = prop_bookings.count()
        nights_sold    = prop_bookings.aggregate(total=Sum('nights'))['total'] or 0

        property_stats.append({
            'property':        prop,
            'revenue':         revenue,
            'bookings_count':  bookings_count,
            'nights_sold':     nights_sold,
            'avg_per_booking': (revenue / bookings_count) if bookings_count else 0,
        })

    # Sort by revenue, highest first — so "top performer" is obvious
    property_stats.sort(key=lambda x: x['revenue'], reverse=True)

    # ── Overall totals across ALL of the owner's properties ──
    total_revenue      = confirmed_bookings.aggregate(total=Sum('grand_total'))['total'] or 0
    total_bookings     = confirmed_bookings.count()
    total_nights       = confirmed_bookings.aggregate(total=Sum('nights'))['total'] or 0
    avg_booking_value  = (total_revenue / total_bookings) if total_bookings else 0

    # ── Data for charts (Chart.js needs JSON arrays) ──────────
    chart_labels   = [stat['property'].name for stat in property_stats]
    chart_revenue  = [float(stat['revenue']) for stat in property_stats]
    chart_bookings = [stat['bookings_count'] for stat in property_stats]

    # ── Monthly revenue trend for the last 6 months ───────────
    # Pure Python month-stepping, no external date libraries needed.
    today = date.today()
    monthly_labels  = []
    monthly_revenue = []

    # Build a list of the 6 most recent (year, month) pairs, oldest first
    months = []
    y, m = today.year, today.month
    for _ in range(6):
        months.append((y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    months.reverse()

    for (year, month) in months:
        month_start = date(year, month, 1)
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)

        month_total = confirmed_bookings.filter(
            created_at__date__gte=month_start,
            created_at__date__lt=next_month
        ).aggregate(total=Sum('grand_total'))['total'] or 0

        monthly_labels.append(calendar.month_abbr[month])
        monthly_revenue.append(float(month_total))

    currency, rate = _get_currency_context(request)
    return render(request, 'properties/owner_revenue.html', {
        'property_stats':       property_stats,
        'total_revenue':        total_revenue,
        'total_bookings':       total_bookings,
        'total_nights':         total_nights,
        'avg_booking_value':    avg_booking_value,
        'top_property':         property_stats[0] if property_stats else None,
        'chart_labels_json':    json.dumps(chart_labels),
        'chart_revenue_json':   json.dumps(chart_revenue),
        'chart_bookings_json':  json.dumps(chart_bookings),
        'monthly_labels_json':  json.dumps(monthly_labels),
        'monthly_revenue_json': json.dumps(monthly_revenue),
        'currency':             currency,
        'rate':                 rate,
    })

@login_required
def traveller_dashboard(request):
    bookings = request.user.bookings.all().order_by('-created_at')
    # Use date.today() — check_in is a DateField, not DateTimeField
    upcoming = bookings.filter(check_in__gte=date.today(), status='confirmed').order_by('check_in')
    # cart_count = 1 if cart has a property selected (i.e. is active), else 0
    try:
        cart = request.user.cart
        cart_count = 1 if (cart.booking_property_id is not None) else 0
    except Exception:
        cart_count = 0
    total_spent_usd = bookings.filter(status='confirmed').aggregate(Sum('grand_total'))['grand_total__sum'] or 0

    currency, rate = _get_currency_context(request)
    if currency == 'TZS':
        total_spent_display = 'TSh {:,.0f}'.format(float(total_spent_usd) * rate)
    else:
        total_spent_display = '${:.2f}'.format(float(total_spent_usd))

    context = {
        'total_bookings':    bookings.count(),
        'upcoming_count':    upcoming.count(),
        'cart_count':        cart_count,
        'total_spent_usd':   float(total_spent_usd),
        'total_spent_display': total_spent_display,
        'upcoming_bookings': upcoming[:5],
        'recent_activity':   bookings[:6],
        'currency':          currency,
        'rate':              rate,
    }
    return render(request, 'properties/traveller_dashboard.html', context)

# ─── WISHLIST & RECENTLY VIEWED ──────────────────────────

@login_required
def wishlist_toggle(request, slug):
    """AJAX POST — adds/removes a property from the current user's wishlist."""
    from django.http import JsonResponse
    from .models import Wishlist

    prop = get_object_or_404(Property, slug=slug, status='active')
    item, created = Wishlist.objects.get_or_create(user=request.user, property=prop)
    if not created:
        item.delete()
        saved = False
    else:
        saved = True

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'saved': saved, 'count': request.user.wishlist_items.count()})

    messages.success(request, "Saved to your wishlist." if saved else "Removed from your wishlist.")
    return redirect('properties:detail', slug=slug)


@login_required
def wishlist_page(request):
    from .models import Wishlist
    items = Wishlist.objects.filter(user=request.user).select_related('property').prefetch_related('property__images')
    currency, rate = _get_currency_context(request)
    return render(request, 'properties/wishlist.html', {
        'items': items,
        'currency': currency,
        'rate': rate,
    })


@login_required
def recently_viewed_page(request):
    from .models import RecentlyViewed
    items = RecentlyViewed.objects.filter(user=request.user).select_related('property').prefetch_related('property__images')[:12]
    currency, rate = _get_currency_context(request)
    return render(request, 'properties/recently_viewed.html', {
        'items': items,
        'currency': currency,
        'rate': rate,
    })
