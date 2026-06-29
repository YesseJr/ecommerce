from django.shortcuts import render, get_object_or_404, redirect
from apps.accounts.decorators import crm_required
from django.contrib import messages
from django.db.models import Sum
from .models import Expense
from .forms import ExpenseForm

@crm_required
def expense_list(request):
    qs = Expense.objects.select_related('recorded_by')
    month_total = qs.filter(date__month=__import__('datetime').date.today().month).aggregate(t=Sum('amount'))['t'] or 0
    return render(request, 'expenses/list.html', {'expenses': qs[:50], 'month_total': month_total, 'page': 'expenses'})

@crm_required
def expense_create(request):
    form = ExpenseForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        exp = form.save(commit=False)
        exp.recorded_by = request.user
        exp.save()
        messages.success(request, 'Expense recorded.')
        return redirect('expense_list')
    return render(request, 'expenses/form.html', {'form': form, 'title': 'New expense', 'page': 'expenses'})

@crm_required
def expense_update(request, pk):
    exp = get_object_or_404(Expense, pk=pk)
    form = ExpenseForm(request.POST or None, instance=exp)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Expense updated.')
        return redirect('expense_list')
    return render(request, 'expenses/form.html', {'form': form, 'expense': exp, 'title': 'Edit expense', 'page': 'expenses'})

@crm_required
def expense_delete(request, pk):
    exp = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        exp.delete()
        messages.success(request, 'Expense deleted.')
        return redirect('expense_list')
    return render(request, 'expenses/confirm_delete.html', {'expense': exp, 'page': 'expenses'})
