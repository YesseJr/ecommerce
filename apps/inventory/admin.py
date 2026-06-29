from django.contrib import admin
from .models import Fragrance
@admin.register(Fragrance)
class FragranceAdmin(admin.ModelAdmin):
    list_display = ["name","brand","sku","concentration","bottle_size","price","stock_quantity","is_low_stock","is_active"]
    list_filter = ["concentration","bottle_size","is_active"]
    search_fields = ["name","brand","sku"]
