from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from .models import Property, PropertyImage, Amenity, PropertyAmenity, PropertyExtra


class PropertyImageInline(admin.TabularInline):
    model           = PropertyImage
    extra           = 3
    fields          = ['image', 'is_primary', 'caption', 'image_preview']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:60px; border-radius:8px;"/>',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Preview'


class PropertyExtraInline(admin.TabularInline):
    model  = PropertyExtra
    extra  = 2
    fields = ['name', 'price', 'charge_type', 'is_available']


class PropertyAmenityInline(admin.TabularInline):
    model = PropertyAmenity
    extra = 3


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = [
        'property_thumbnail', 'name', 'owner',
        'property_type', 'city', 'price_per_night',
        'status_badge', 'is_available', 'created_at'
    ]
    list_filter       = ['property_type', 'status', 'is_available', 'city']
    search_fields     = ['name', 'city', 'owner__username']
    prepopulated_fields = {'slug': ('name',)}
    inlines           = [PropertyImageInline, PropertyExtraInline, PropertyAmenityInline]

    # ✅ Status now editable directly from the list
    list_editable     = ['is_available']
    ordering          = ['-created_at']
    readonly_fields   = ['created_at', 'updated_at', 'average_rating_display']

    # ✅ Bulk actions for approving/rejecting properties
    actions = [
        'approve_properties',
        'reject_properties',
        'mark_inactive',
    ]

    fieldsets = (
        ('Basic Info', {
            'fields': ('owner', 'name', 'slug', 'property_type', 'description', 'status')
        }),
        ('Location', {
            'fields': ('country', 'city', 'address', 'latitude', 'longitude')
        }),
        ('Pricing & Capacity', {
            'fields': ('price_per_night', 'max_guests', 'bedrooms', 'bathrooms', 'is_available')
        }),
        ('Stats', {
            'fields': ('average_rating_display', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # ─── BULK ACTIONS ───────────────────────────────────

    @admin.action(description='✅ Approve selected properties')
    def approve_properties(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(
            request,
            f'{updated} propert{"y" if updated == 1 else "ies"} approved and set to Active.',
            messages.SUCCESS
        )

    @admin.action(description='❌ Reject selected properties')
    def reject_properties(self, request, queryset):
        updated = queryset.update(status='inactive')
        self.message_user(
            request,
            f'{updated} propert{"y" if updated == 1 else "ies"} rejected and set to Inactive.',
            messages.WARNING
        )

    @admin.action(description='⏸ Mark selected properties as Inactive')
    def mark_inactive(self, request, queryset):
        updated = queryset.update(status='inactive', is_available=False)
        self.message_user(
            request,
            f'{updated} propert{"y" if updated == 1 else "ies"} marked as Inactive.',
            messages.WARNING
        )

    # ─── CUSTOM DISPLAY METHODS ─────────────────────────

    def property_thumbnail(self, obj):
        img = obj.images.filter(is_primary=True).first() or obj.images.first()
        if img:
            return format_html(
                '<img src="{}" style="height:45px; width:65px; '
                'object-fit:cover; border-radius:8px;"/>',
                img.image.url
            )
        return format_html('<span style="color:#ccc;">No image</span>')
    property_thumbnail.short_description = ''

    def status_badge(self, obj):
        colors = {
            'active':   ('#dcfce7', '#15803d'),
            'pending':  ('#fff7ed', '#c2410c'),
            'inactive': ('#f3f4f6', '#6b7280'),
        }
        bg, text = colors.get(obj.status, ('#f3f4f6', '#6b7280'))
        return format_html(
            '<span style="background:{}; color:{}; padding:4px 12px; '
            'border-radius:999px; font-size:11px; font-weight:700;">{}</span>',
            bg, text,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def average_rating_display(self, obj):
        rating = obj.average_rating()
        if rating:
            return format_html(
                '<strong>⭐ {}</strong> ({} reviews)',
                rating,
                obj.total_reviews()
            )
        return "No reviews yet"
    average_rating_display.short_description = 'Rating'


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display  = ['image_preview', 'property', 'is_primary', 'caption', 'uploaded_at']
    list_filter   = ['is_primary']
    search_fields = ['property__name']

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:40px; width:60px; '
                'object-fit:cover; border-radius:6px;"/>',
                obj.image.url
            )
        return "—"
    image_preview.short_description = ''


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display  = ['name', 'icon']
    search_fields = ['name']


@admin.register(PropertyExtra)
class PropertyExtraAdmin(admin.ModelAdmin):
    list_display  = [
        'name', 'property', 'price_display',
        'charge_type', 'is_available'
    ]
    list_filter   = ['charge_type', 'is_available']
    list_editable = ['is_available']
    search_fields = ['name', 'property__name']

    def price_display(self, obj):
        return format_html(
            '<strong style="color:#f97316;">${}</strong>',
            obj.price
        )
    price_display.short_description = 'Price'