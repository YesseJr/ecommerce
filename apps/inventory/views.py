from django.shortcuts import render, get_object_or_404, redirect
from apps.accounts.decorators import crm_required
from django.contrib import messages
from django.db.models import Q
from .models import Fragrance
from .forms import FragranceForm

@crm_required
def fragrance_list(request):
    qs = Fragrance.objects.filter(is_active=True)
    q = request.GET.get('q', '')
    low = request.GET.get('low', '')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(brand__icontains=q) | Q(sku__icontains=q))
    items = list(qs)
    if low:
        items = [f for f in items if f.is_low_stock]
    low_stock_count = sum(1 for f in Fragrance.objects.filter(is_active=True) if f.is_low_stock)
    return render(request, 'inventory/list.html', {
        'fragrances': items, 'q': q, 'low_filter': low,
        'low_stock_count': low_stock_count, 'page': 'inventory'
    })

@crm_required
def fragrance_create(request):
    form = FragranceForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Fragrance added to inventory.')
        return redirect('fragrance_list')
    return render(request, 'inventory/form.html', {'form': form, 'title': 'Add fragrance', 'page': 'inventory'})

@crm_required
def fragrance_update(request, pk):
    frag = get_object_or_404(Fragrance, pk=pk)
    form = FragranceForm(request.POST or None, request.FILES or None, instance=frag)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Fragrance updated.')
        return redirect('fragrance_list')
    return render(request, 'inventory/form.html', {'form': form, 'fragrance': frag, 'title': 'Edit fragrance', 'page': 'inventory'})

@crm_required
def fragrance_delete(request, pk):
    frag = get_object_or_404(Fragrance, pk=pk)
    if request.method == 'POST':
        frag.is_active = False
        frag.save()
        messages.success(request, f'{frag.name} deactivated.')
        return redirect('fragrance_list')
    return render(request, 'inventory/confirm_delete.html', {'fragrance': frag, 'page': 'inventory'})
