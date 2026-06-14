from django.contrib import admin
from django.utils.html import format_html
from .models import Cart, CartItem, Booking, BookingExtra


class BookingExtraInline(admin.TabularInline):
    model           = BookingExtra
    extra           = 0
    readonly_fields = ['extra_name', 'extra_price', 'charge_type', 'subtotal']
    can_delete      = False


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'reference', 'traveller', 'property_name',
        'check_in', 'check_out', 'nights',
        'grand_total_display', 'status_badge', 'created_at'
    ]
    list_filter   = ['status', 'created_at']
    search_fields = ['reference', 'traveller__username', 'booking_property__name']
    readonly_fields = [
        'reference', 'nights', 'room_total',
        'extras_total', 'grand_total', 'created_at', 'updated_at'
    ]
    inlines  = [BookingExtraInline]
    ordering = ['-created_at']

    fieldsets = (
        ('Booking Info', {
            'fields': ('reference', 'traveller', 'booking_property', 'status')
        }),
        ('Dates & Guests', {
            'fields': ('check_in', 'check_out', 'nights', 'guests')
        }),
        ('Pricing', {
            'fields': ('price_per_night', 'room_total', 'extras_total', 'grand_total')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def property_name(self, obj):
        return obj.booking_property.name
    property_name.short_description = 'Property'

    def grand_total_display(self, obj):
        return format_html(
            '<strong style="color:#f97316;">${}</strong>',
            obj.grand_total
        )
    grand_total_display.short_description = 'Total'

    def status_badge(self, obj):
        colors = {
            'confirmed': '#22c55e',
            'pending':   '#f97316',
            'cancelled': '#ef4444',
            'completed': '#1B3A6B',
        }
        color = colors.get(obj.status, '#9ca3af')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; '
            'border-radius:999px; font-size:11px; font-weight:600;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display  = [
        'traveller', 'booking_property',
        'check_in', 'check_out',
        'guests', 'updated_at'
    ]
    search_fields = ['traveller__username']


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display  = ['cart', 'extra', 'added_at']
    search_fields = ['cart__traveller__username', 'extra__name']