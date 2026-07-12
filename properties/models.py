from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import User


# Curated, Dar es Salaam–wide list of well-known wards/neighborhoods,
# grouped by municipality for the "List Property" dropdown. Kept as a
# module-level constant (not DB choices) so existing free-text values
# and future areas aren't blocked by a hard schema constraint.
DAR_NEIGHBORHOODS = [
    ('Kinondoni', [
        ('Msasani', 'Msasani'),
        ('Masaki', 'Masaki'),
        ('Oyster Bay', 'Oyster Bay'),
        ('Mikocheni', 'Mikocheni'),
        ('Kijitonyama', 'Kijitonyama'),
        ('Sinza', 'Sinza'),
        ('Magomeni', 'Magomeni'),
        ('Manzese', 'Manzese'),
        ('Tandale', 'Tandale'),
        ('Kawe', 'Kawe'),
        ('Mbezi Beach', 'Mbezi Beach'),
        ('Kunduchi', 'Kunduchi'),
        ('Makumbusho', 'Makumbusho'),
    ]),
    ('Ilala', [
        ('Kariakoo', 'Kariakoo'),
        ('Upanga', 'Upanga'),
        ('Ilala', 'Ilala'),
        ('Buguruni', 'Buguruni'),
        ('Vingunguti', 'Vingunguti'),
        ('Segerea', 'Segerea'),
        ('Tabata', 'Tabata'),
        ('Kipawa', 'Kipawa'),
        ('Chanika', 'Chanika'),
    ]),
    ('Temeke', [
        ('Temeke', 'Temeke'),
        ('Mbagala', 'Mbagala'),
        ('Kurasini', 'Kurasini'),
        ("Chang'ombe", "Chang'ombe"),
        ('Miburani', 'Miburani'),
        ('Charambe', 'Charambe'),
    ]),
    ('Ubungo', [
        ('Ubungo', 'Ubungo'),
        ('Kimara', 'Kimara'),
        ('Kimara Bonyokwa', 'Kimara Bonyokwa'),
        ('Mbezi Luis', 'Mbezi Luis'),
        ('Kibamba', 'Kibamba'),
        ('Kwembe', 'Kwembe'),
        ('Goba', 'Goba'),
    ]),
    ('Kigamboni', [
        ('Kigamboni', 'Kigamboni'),
        ('Vijibweni', 'Vijibweni'),
        ('Kibada', 'Kibada'),
        ('Somangila', 'Somangila'),
    ]),
]


class Property(models.Model):

    PROPERTY_TYPES = [
        ('hotel', 'Hotel'),
        ('apartment', 'Apartment'),
        ('guesthouse', 'Guest House'),
        ('villa', 'Villa'),
        ('hostel', 'Hostel'),
        ('resort', 'Resort'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending Review'),
    ]

    CANCELLATION_POLICIES = [
        ('flexible', 'Flexible — full refund up to 24h before check-in'),
        ('moderate', 'Moderate — full refund up to 5 days before check-in'),
        ('strict',   'Strict — 50% refund up to 7 days before check-in'),
    ]

    # Ownership
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='properties'
    )

    # Basic Info
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    property_type = models.CharField(
        max_length=20,
        choices=PROPERTY_TYPES,
        default='hotel'
    )
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # Location
    country = models.CharField(max_length=100, default='Tanzania')
    city = models.CharField(max_length=100)
    neighborhood = models.CharField(
        max_length=100, blank=True,
        help_text="Area within the city, e.g. Kigamboni, Tabata, Masaki, Mikocheni."
    )
    address = models.TextField()
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )

    # Pricing
    price_per_night = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    # Details
    max_guests = models.PositiveIntegerField(default=2)
    bedrooms = models.PositiveIntegerField(default=1)
    bathrooms = models.PositiveIntegerField(default=1)
    is_available = models.BooleanField(default=True)

    # ── Trust, policy & business fields ────────────────────
    is_verified = models.BooleanField(
        default=False,
        help_text="Verified by BookMyStay staff (ID + ownership checked)."
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Curated placement on the homepage. Set by admins."
    )
    house_rules = models.TextField(
        blank=True,
        help_text="e.g. No smoking, No parties, Check-in after 2PM."
    )
    accessibility_features = models.TextField(
        blank=True,
        help_text="e.g. Step-free entrance, Elevator access, Wide doorways."
    )
    cancellation_policy = models.CharField(
        max_length=20,
        choices=CANCELLATION_POLICIES,
        default='moderate'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Properties'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.city}"

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return None

    @property
    def total_reviews(self):
        return self.reviews.count()


class PropertyImage(models.Model):
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='properties/')
    is_primary = models.BooleanField(default=False)
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.property.name}"


class Amenity(models.Model):
    AMENITY_ICONS = [
        ('wifi', '📶 WiFi'),
        ('parking', '🅿️ Parking'),
        ('ac', '❄️ Air Conditioning'),
        ('kitchen', '🍳 Kitchen'),
        ('tv', '📺 TV'),
        ('washer', '🫧 Washer'),
        ('heating', '🔥 Heating'),
        ('workspace', '💻 Workspace'),
    ]

    name = models.CharField(max_length=100)
    icon = models.CharField(
        max_length=20,
        choices=AMENITY_ICONS,
        blank=True
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Amenities'


class PropertyAmenity(models.Model):
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='amenities'
    )
    amenity = models.ForeignKey(
        Amenity,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.property.name} - {self.amenity.name}"


class PropertyExtra(models.Model):
    CHARGE_TYPES = [
        ('per_night', 'Per Night'),
        ('once', 'One Time'),
        ('per_person', 'Per Person'),
    ]

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='extras'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    charge_type = models.CharField(
        max_length=20,
        choices=CHARGE_TYPES,
        default='per_night'
    )
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.property.name}"


class Wishlist(models.Model):
    """A guest's saved properties — the persisted 'heart' save."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='wishlist_items'
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='wishlisted_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'property']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} ♥ {self.property.name}"


class RecentlyViewed(models.Model):
    """Tracks the last properties a guest looked at, most-recent first."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recently_viewed'
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='viewed_by'
    )
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'property']
        ordering = ['-viewed_at']

    def __str__(self):
        return f"{self.user.username} viewed {self.property.name}"

# ─── ADD this helper function to properties/models.py ───
# Place it at the bottom of the file, outside any class

def check_property_availability(property_obj, check_in, check_out, exclude_booking_id=None):
    """
    Returns True if the property is available for the given date range.
    Returns False if there's an overlapping CONFIRMED booking.

    Two date ranges overlap when:
        existing.check_in  <  new.check_out
        AND
        existing.check_out >  new.check_in
    """
    from bookings.models import Booking  # local import avoids circular import

    overlapping = Booking.objects.filter(
        booking_property=property_obj,
        status='confirmed',
        check_in__lt=check_out,
        check_out__gt=check_in,
    )

    if exclude_booking_id:
        overlapping = overlapping.exclude(pk=exclude_booking_id)

    return not overlapping.exists()


def get_unavailable_dates(property_obj):
    """
    Returns a list of {check_in, check_out} dicts for all
    confirmed bookings on this property — used to disable
    those dates on the booking calendar in the frontend.
    """
    from bookings.models import Booking

    bookings = Booking.objects.filter(
        booking_property=property_obj,
        status='confirmed'
    ).values('check_in', 'check_out')

    return [
        {
            'check_in':  b['check_in'].isoformat(),
            'check_out': b['check_out'].isoformat(),
        }
        for b in bookings
    ]


def get_similar_properties(property_obj, limit=4):
    """
    Lightweight recommendation: same city or same type, similar price band,
    excluding the property itself. No ML needed — ranks by a simple
    relevance score (city match + type match + review quality).
    """
    from django.db.models import Case, When, Value, IntegerField, Avg

    from decimal import Decimal
    price = property_obj.price_per_night
    low, high = price * Decimal('0.5'), price * Decimal('1.8')

    candidates = Property.objects.filter(
        status='active', is_available=True
    ).exclude(pk=property_obj.pk).filter(
        models.Q(city=property_obj.city) |
        models.Q(property_type=property_obj.property_type) |
        models.Q(price_per_night__gte=low, price_per_night__lte=high)
    ).annotate(
        relevance=Case(
            When(city=property_obj.city, property_type=property_obj.property_type, then=Value(3)),
            When(city=property_obj.city, then=Value(2)),
            When(property_type=property_obj.property_type, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    ).order_by('-relevance', '-created_at')[:limit]

    return candidates