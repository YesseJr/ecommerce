from django.shortcuts import render, get_object_or_404, redirect
from apps.accounts.decorators import crm_required
from django.contrib import messages
from django.db.models import Q
from .models import Company
from .forms import CompanyForm

@crm_required
def company_list(request):
    qs = Company.objects.all()
    q = request.GET.get('q', '')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(city__icontains=q))
    return render(request, 'companies/list.html', {'companies': qs, 'q': q, 'page': 'accounts_co'})

@crm_required
def company_create(request):
    form = CompanyForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Account created.')
        return redirect('company_list')
    return render(request, 'companies/form.html', {'form': form, 'title': 'New account', 'page': 'accounts_co'})

@crm_required
def company_update(request, pk):
    company = get_object_or_404(Company, pk=pk)
    form = CompanyForm(request.POST or None, instance=company)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Account updated.')
        return redirect('company_list')
    return render(request, 'companies/form.html', {'form': form, 'company': company, 'title': 'Edit account', 'page': 'accounts_co'})

@crm_required
def company_delete(request, pk):
    co = get_object_or_404(Company, pk=pk)
    if request.method == 'POST':
        co.delete()
        messages.success(request, 'Account deleted.')
        return redirect('company_list')
    return render(request, 'companies/confirm_delete.html', {'company': co, 'page': 'accounts_co'})
