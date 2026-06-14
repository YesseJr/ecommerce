from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.text import slugify
from django.db.models import Q
from .models import Property, PropertyImage, PropertyExtra, Amenity
from .forms import PropertyForm, PropertyExtraForm
from datetime import date


# ─── PUBLIC VIEWS ───────────────────────────────────────


def home(request):
    featured = Property.objects.filter(
        status='active',
        is_available=True
    ).order_by('-created_at')[:6]

    cities = Property.objects.filter(
        status='active'
    ).values_list('city', flat=True).distinct()

    return render(request, 'properties/home.html', {
        'featured': featured,
        'cities': cities,
        'property_types': Property.PROPERTY_TYPES,  # 👈 add this
    })

def property_list(request):
    properties = Property.objects.filter(
        status='active',
        is_available=True
    )

    # Search & Filter
    query     = request.GET.get('q', '')
    city      = request.GET.get('city', '')
    prop_type = request.GET.get('type', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    guests    = request.GET.get('guests', '')

    if query:
        properties = properties.filter(
            Q(name__icontains=query) |
            Q(city__icontains=query) |
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

    cities = Property.objects.filter(
        status='active'
    ).values_list('city', flat=True).distinct()

    return render(request, 'properties/list.html', {
        'properties': properties,
        'cities': cities,
        'property_types': Property.PROPERTY_TYPES,
        'filters': {
            'q': query, 'city': city,
            'type': prop_type, 'min_price': min_price,
            'max_price': max_price, 'guests': guests,
        }
    })


def property_detail(request, slug):
    # Owners can preview their own pending properties
    # Everyone else only sees active ones
    if request.user.is_authenticated and request.user.is_owner:
        prop = get_object_or_404(
            Property,
            slug=slug,
            owner=request.user
        )
    else:
        prop = get_object_or_404(
            Property,
            slug=slug,
            status='active'
        )

    extras  = prop.extras.filter(is_available=True)
    images  = prop.images.all()
    reviews = prop.reviews.all().order_by('-created_at')[:5]

    return render(request, 'properties/detail.html', {
        'property': prop,
        'extras':   extras,
        'images':   images,
        'reviews':  reviews,
        'today':    date.today().isoformat(),
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

    return render(request, 'properties/owner_dashboard.html', {
        'properties': properties,
        'total': total,
        'active': active,
        'pending': pending,
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
        form = PropertyForm(request.POST, request.FILES, instance=prop)
        if form.is_valid():
            form.save()

            # Handle new image uploads
            images = request.FILES.getlist('images')
            for i, image in enumerate(images):
                PropertyImage.objects.create(
                    property=prop,
                    image=image,
                    is_primary=False
                )

            messages.success(request, "Property updated successfully! ✅")
            return redirect('properties:owner_dashboard')
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

    return render(request, 'properties/manage_extras.html', {
        'property': prop,
        'extras': extras,
        'form': form,
    })


@login_required
def delete_extra(request, pk):
    extra = get_object_or_404(PropertyExtra, pk=pk, property__owner=request.user)
    slug = extra.property.slug
    extra.delete()
    messages.success(request, "Extra removed.")
    return redirect('properties:manage_extras', slug=slug)