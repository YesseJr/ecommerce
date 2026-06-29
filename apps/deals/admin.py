from django.contrib import admin
from .models import Deal
@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ["title","contact","value","stage","assigned_to","created_at"]
    list_filter = ["stage","source"]
