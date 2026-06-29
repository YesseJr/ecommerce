from django.shortcuts import render
from apps.accounts.decorators import crm_required
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from apps.sales.models import Sale
from apps.expenses.models import Expense
from apps.contacts.models import Contact

@crm_required
def reports_index(request):
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    revenue = Sale.objects.filter(status='completed', created_at__gte=month_start).aggregate(t=Sum('total'))['t'] or 0
    expenses = Expense.objects.filter(date__month=now.month, date__year=now.year).aggregate(t=Sum('amount'))['t'] or 0
    profit = revenue - expenses
    top_contacts = Contact.objects.annotate(
        ltv=Sum('sale__total')
    ).filter(ltv__isnull=False).order_by('-ltv')[:10]
    return render(request, 'reports/index.html', {
        'revenue': revenue, 'expenses': expenses, 'profit': profit,
        'top_contacts': top_contacts, 'page': 'reports'
    })
