from django.contrib import admin
from .models import Contact

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'city', 'status', 'loyalty_points', 'created_at']
    list_filter = ['status', 'city']
    search_fields = ['first_name', 'last_name', 'phone', 'email']
