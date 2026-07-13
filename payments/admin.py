from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from .models import Payment, CurrencyConfig, Coupon


# ─── CurrencyConfig Admin ─────────────────────────────────────────────────────

@admin.register(CurrencyConfig)
class CurrencyConfigAdmin(admin.ModelAdmin):
    """
    Admin for managing exchange rates and enabling/disabling currencies.
    Only one record (pk=1) should exist — the singleton.
    """
    list_display = ['rate_display', 'usd_status', 'tzs_status', 'updated_at']
    readonly_fields = ['updated_at', 'rate_preview']

    fieldsets = (
        ('💱 Exchange Rate', {
            'fields': ('usd_to_tzs', 'rate_preview'),
            'description': 'Set the exchange rate used for currency conversion throughout the site.',
        }),
        ('✅ Enabled Currencies', {
            'fields': ('usd_enabled', 'tzs_enabled'),
        }),
        ('📋 Metadata', {
            'fields': ('updated_at',),
            'classes': ('collapse',),
        }),
    )

    def rate_display(self, obj):
        return format_html(
            '<strong style="color:#f97316; font-size:15px;">1 USD = {} TZS</strong>',
            obj.usd_to_tzs
        )
    rate_display.short_description = 'Current Rate'

    def rate_preview(self, obj):
        return format_html(
            '<div style="background:#fff7ed;border:1px solid #fed7aa;padding:12px;border-radius:8px;">'
            '<b>Preview:</b><br>'
            '&nbsp;&nbsp;$100 USD = <b>TSh {:,.0f}</b> TZS<br>'
            '&nbsp;&nbsp;$250 USD = <b>TSh {:,.0f}</b> TZS<br>'
            '&nbsp;&nbsp;$500 USD = <b>TSh {:,.0f}</b> TZS'
            '</div>',
            100 * obj.usd_to_tzs,
            250 * obj.usd_to_tzs,
            500 * obj.usd_to_tzs,
        )
    rate_preview.short_description = 'Live Preview'

    def usd_status(self, obj):
        if obj.usd_enabled:
            return format_html('<span style="color:#22c55e;font-weight:700;">✓ Enabled</span>')
        return format_html('<span style="color:#ef4444;font-weight:700;">✗ Disabled</span>')
    usd_status.short_description = 'USD ($)'

    def tzs_status(self, obj):
        if obj.tzs_enabled:
            return format_html('<span style="color:#22c55e;font-weight:700;">✓ Enabled</span>')
        return format_html('<span style="color:#ef4444;font-weight:700;">✗ Disabled</span>')
    tzs_status.short_description = 'TZS (TSh)'

    def has_add_permission(self, request):
        # Only allow one record
        return not CurrencyConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


# ─── Payment Admin ────────────────────────────────────────────────────────────

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_id_short', 'traveller_name', 'booking_ref',
        'amount_display', 'currency_badge', 'method_badge',
        'status_badge', 'payment_date',
    ]
    list_filter   = ['status', 'payment_method', 'currency', 'created_at']
    search_fields = [
        'transaction_id', 'receipt_number', 'authorization_code',
        'traveller__username', 'traveller__email', 'booking__reference',
    ]
    readonly_fields = [
        'transaction_id', 'authorization_code', 'receipt_number',
        'payment_date', 'created_at', 'updated_at',
        'amount_usd', 'exchange_rate', 'payment_details_panel',
    ]
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('📋 Booking', {
            'fields': ('booking', 'traveller'),
        }),
        ('💳 Payment Method', {
            'fields': ('payment_method', 'provider', 'payment_details_panel'),
        }),
        ('💱 Currency & Amount', {
            'fields': ('currency', 'amount', 'exchange_rate', 'amount_usd'),
        }),
        ('🔑 Transaction References', {
            'fields': ('transaction_id', 'authorization_code', 'receipt_number'),
        }),
        ('📊 Status & Timestamps', {
            'fields': ('status', 'payment_date', 'created_at', 'updated_at'),
        }),
    )

    # ── Column renderers ──────────────────────────────────────────────────────

    def transaction_id_short(self, obj):
        if obj.transaction_id:
            return format_html(
                '<code style="font-size:11px;color:#6366f1;">{}</code>',
                obj.transaction_id[:20] + '…' if len(obj.transaction_id) > 20 else obj.transaction_id
            )
        return '—'
    transaction_id_short.short_description = 'Transaction ID'

    def traveller_name(self, obj):
        return format_html(
            '<strong>{}</strong><br><span style="color:#9ca3af;font-size:11px;">{}</span>',
            obj.traveller.get_full_name() or obj.traveller.username,
            obj.traveller.email,
        )
    traveller_name.short_description = 'Traveller'

    def booking_ref(self, obj):
        return format_html(
            '<span style="font-family:monospace;font-weight:700;color:#1B3A6B;">{}</span>',
            obj.booking.reference
        )
    booking_ref.short_description = 'Booking Ref'

    def amount_display(self, obj):
        symbol = 'TSh' if obj.currency == 'TZS' else '$'
        fmt    = f"{obj.amount:,.0f}" if obj.currency == 'TZS' else f"{obj.amount:,.2f}"
        return format_html(
            '<strong style="color:#f97316;font-size:14px;">{} {}</strong>'
            '<br><span style="color:#9ca3af;font-size:11px;">${} USD</span>',
            symbol, fmt, f"{obj.amount_usd:,.2f}"
        )
    amount_display.short_description = 'Amount'

    def currency_badge(self, obj):
        color = '#3b82f6' if obj.currency == 'USD' else '#10b981'
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;'
            'border-radius:999px;font-size:11px;font-weight:700;">{}</span>',
            color, obj.currency
        )
    currency_badge.short_description = 'Currency'

    def method_badge(self, obj):
        colors = {
            'credit_card': '#3b82f6',
            'debit_card':  '#6366f1',
            'mpesa':       '#22c55e',
            'airtel':      '#ef4444',
            'tigo':        '#0ea5e9',
            'halopesa':    '#f59e0b',
            'card':        '#3b82f6',
            'cash':        '#f59e0b',
        }
        color = colors.get(obj.payment_method, '#9ca3af')
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;'
            'border-radius:999px;font-size:11px;font-weight:600;">{}</span>',
            color, obj.get_method_display()
        )
    method_badge.short_description = 'Method'

    def status_badge(self, obj):
        colors = {
            'success':    '#22c55e',
            'pending':    '#f97316',
            'processing': '#3b82f6',
            'failed':     '#ef4444',
            'refunded':   '#8b5cf6',
            'cancelled':  '#6b7280',
        }
        color = colors.get(obj.status, '#9ca3af')
        label = dict(Payment.STATUS_CHOICES).get(obj.status, obj.status)
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;'
            'border-radius:999px;font-size:11px;font-weight:700;">{}</span>',
            color, label
        )
    status_badge.short_description = 'Status'

    def payment_details_panel(self, obj):
        if obj.is_card():
            return format_html(
                '<div style="background:#eff6ff;border:1px solid #bfdbfe;padding:10px;border-radius:8px;">'
                '<b>💳 Card Payment</b><br>'
                'Auth Code: <code>{}</code>'
                '</div>',
                obj.authorization_code or '—'
            )
        elif obj.is_mobile_money():
            return format_html(
                '<div style="background:#f0fdf4;border:1px solid #bbf7d0;padding:10px;border-radius:8px;">'
                '<b>📱 Mobile Money</b><br>'
                'Provider: <strong>{}</strong><br>'
                'Receipt: <code>{}</code>'
                '</div>',
                obj.provider or '—',
                obj.receipt_number or '—'
            )
        return '—'
    payment_details_panel.short_description = 'Payment Details'


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'used_count', 'max_uses', 'active', 'valid_from', 'valid_to']
    list_filter = ['discount_type', 'active']
    search_fields = ['code']
    list_editable = ['active']
