from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        'traveller', 'property',
        'rating', 'cleanliness',
        'location', 'value',
        'title', 'created_at'
    ]
    list_filter = ['rating', 'created_at']
    search_fields = [
        'traveller__username',
        'property__name',
        'title'
    ]
    readonly_fields = ['created_at']
    ordering = ['-created_at']