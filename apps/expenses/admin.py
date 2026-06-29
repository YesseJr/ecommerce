from django.contrib import admin
from .models import Expense
@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ["title","category","amount","date","recorded_by"]
    list_filter = ["category","payment_method"]
