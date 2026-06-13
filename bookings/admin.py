from django.contrib import admin
from .models import Cart, CartItem, Booking, BookingExtra


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ['extra', 'added_at']
    readonly_fields = ['added_at']


class BookingExtraInline(admin.TabularInline):
    model = BookingExtra
    extra = 0
    fields = ['extra_name', 'extra_price', 'charge_type', 'subtotal']
    readonly_fields = ['extra_name', 'extra_price', 'charge_type', 'subtotal']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = [
        'traveller', 'booking_property',
        'check_in', 'check_out',
        'guests', 'updated_at'
    ]
    search_fields = ['traveller__username']
    inlines = [CartItemInline]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'reference', 'traveller', 'booking_property',
        'check_in', 'check_out', 'nights',
        'grand_total', 'status', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = [
        'reference',
        'traveller__username',
        'booking_property__name'
    ]
    readonly_fields = [
        'reference', 'nights', 'room_total',
        'extras_total', 'grand_total', 'created_at'
    ]
    inlines = [BookingExtraInline]
    list_editable = ['status']
    ordering = ['-created_at']