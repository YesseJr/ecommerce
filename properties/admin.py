from django.contrib import admin
from django.utils.html import format_html
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
    list_editable     = ['is_available']
    ordering          = ['-created_at']
    readonly_fields   = ['created_at', 'updated_at', 'average_rating_display']

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

    def property_thumbnail(self, obj):
        img = obj.images.filter(is_primary=True).first() or obj.images.first()
        if img:
            return format_html(
                '<img src="{}" style="height:45px; width:65px; object-fit:cover; border-radius:8px;"/>',
                img.image.url
            )
        return format_html('<span style="color:#ccc;">No image</span>')
    property_thumbnail.short_description = ''

    def status_badge(self, obj):
        colors = {
            'active':   '#22c55e',
            'pending':  '#f97316',
            'inactive': '#9ca3af',
        }
        color = colors.get(obj.status, '#9ca3af')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; '
            'border-radius:999px; font-size:11px; font-weight:600;">{}</span>',
            color,
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
    list_display  = ['property', 'is_primary', 'caption', 'uploaded_at']
    list_filter   = ['is_primary']


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display  = ['name', 'icon']
    search_fields = ['name']


@admin.register(PropertyExtra)
class PropertyExtraAdmin(admin.ModelAdmin):
    list_display  = ['name', 'property', 'price', 'charge_type', 'is_available']
    list_filter   = ['charge_type', 'is_available']
    search_fields = ['name', 'property__name']