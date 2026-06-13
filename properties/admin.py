from django.contrib import admin
from .models import Property, PropertyImage, Amenity, PropertyAmenity, PropertyExtra


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 3
    fields = ['image', 'is_primary', 'caption']


class PropertyExtraInline(admin.TabularInline):
    model = PropertyExtra
    extra = 2
    fields = ['name', 'description', 'price', 'charge_type', 'is_available']


class PropertyAmenityInline(admin.TabularInline):
    model = PropertyAmenity
    extra = 3


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'owner', 'property_type',
        'city', 'price_per_night', 'status',
        'is_available', 'created_at'
    ]
    list_filter = ['property_type', 'status', 'is_available', 'city']
    search_fields = ['name', 'city', 'owner__username']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [PropertyImageInline, PropertyExtraInline, PropertyAmenityInline]
    list_editable = ['status', 'is_available']
    ordering = ['-created_at']


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ['property', 'is_primary', 'caption', 'uploaded_at']
    list_filter = ['is_primary']


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon']
    search_fields = ['name']


@admin.register(PropertyExtra)
class PropertyExtraAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'property', 'price',
        'charge_type', 'is_available'
    ]
    list_filter = ['charge_type', 'is_available']
    search_fields = ['name', 'property__name']