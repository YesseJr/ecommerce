from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_id', 'traveller',
        'booking', 'amount', 'method',
        'status', 'paid_at', 'created_at'
    ]
    list_filter = ['method', 'status', 'created_at']
    search_fields = [
        'transaction_id',
        'traveller__username',
        'booking__reference'
    ]
    readonly_fields = [
        'transaction_id', 'paid_at', 'created_at'
    ]
    ordering = ['-created_at']