from django.contrib import admin
from .models import Company
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name","type","city","phone"]
    list_filter = ["type"]
