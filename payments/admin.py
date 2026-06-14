from django.contrib import admin
from django.utils.html import format_html
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display  = [
        'transaction_id', 'traveller',
        'booking_reference', 'amount_display',
        'method_badge', 'status_badge',
        'paid_at'
    ]
    list_filter   = ['method', 'status', 'created_at']
    search_fields = ['transaction_id', 'traveller__username', 'booking__reference']
    readonly_fields = ['transaction_id', 'paid_at', 'created_at']
    ordering      = ['-created_at']

    def booking_reference(self, obj):
        return obj.booking.reference
    booking_reference.short_description = 'Booking Ref'

    def amount_display(self, obj):
        return format_html('<strong style="color:#f97316;">${}</strong>', obj.amount)
    amount_display.short_description = 'Amount'

    def method_badge(self, obj):
        colors = {
            'mpesa':  '#22c55e',
            'airtel': '#ef4444',
            'card':   '#3b82f6',
            'cash':   '#f59e0b',
        }
        color = colors.get(obj.method, '#9ca3af')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; border-radius:999px; font-size:11px; font-weight:600;">{}</span>',
            color,
            obj.get_method_display()
        )
    method_badge.short_description = 'Method'

    def status_badge(self, obj):
        colors = {
            'success':  '#22c55e',
            'pending':  '#f97316',
            'failed':   '#ef4444',
            'refunded': '#8b5cf6',
        }
        color = colors.get(obj.status, '#9ca3af')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; border-radius:999px; font-size:11px; font-weight:600;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'