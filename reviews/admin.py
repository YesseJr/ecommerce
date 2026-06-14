from django.contrib import admin
from django.utils.html import format_html
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display  = [
        'traveller', 'property',
        'rating_stars', 'cleanliness',
        'location', 'value',
        'title', 'created_at'
    ]
    list_filter   = ['rating', 'created_at']
    search_fields = ['traveller__username', 'property__name', 'title']
    readonly_fields = ['created_at']
    ordering      = ['-created_at']

    def rating_stars(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html(
            '<span style="color:#D97706; font-size:16px;">{}</span>',
            stars
        )
    rating_stars.short_description = 'Rating'