from django.shortcuts import render, get_object_or_404, redirect
from apps.accounts.decorators import crm_required
from django.contrib import messages
from django.db.models import Sum, Q
from .models import Deal
from .forms import DealForm

STAGES = ['lead', 'qualified', 'proposal', 'negotiation', 'won', 'lost']

@crm_required
def deal_pipeline(request):
    deals = Deal.objects.select_related('contact', 'company', 'assigned_to')
    columns = {}
    for stage, label in Deal.STAGE_CHOICES:
        stage_deals = deals.filter(stage=stage)
        columns[stage] = {
            'label': label,
            'deals': stage_deals,
            'count': stage_deals.count(),
            'total': stage_deals.aggregate(t=Sum('value'))['t'] or 0,
        }
    pipeline_total = deals.filter(stage__in=['lead','qualified','proposal','negotiation']).aggregate(t=Sum('value'))['t'] or 0
    return render(request, 'deals/pipeline.html', {'columns': columns, 'pipeline_total': pipeline_total, 'page': 'pipeline'})

@crm_required
def deal_list(request):
    qs = Deal.objects.select_related('contact', 'assigned_to')
    q = request.GET.get('q', '')
    stage = request.GET.get('stage', '')
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(contact__first_name__icontains=q))
    if stage:
        qs = qs.filter(stage=stage)
    return render(request, 'deals/list.html', {'deals': qs, 'q': q, 'stage_filter': stage, 'stage_choices': Deal.STAGE_CHOICES, 'page': 'deals'})

@crm_required
def deal_create(request):
    form = DealForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Deal created.')
        return redirect('deal_pipeline')
    return render(request, 'deals/form.html', {'form': form, 'title': 'New deal', 'page': 'deals'})

@crm_required
def deal_update(request, pk):
    deal = get_object_or_404(Deal, pk=pk)
    form = DealForm(request.POST or None, instance=deal)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Deal updated.')
        return redirect('deal_pipeline')
    return render(request, 'deals/form.html', {'form': form, 'deal': deal, 'title': 'Edit deal', 'page': 'deals'})

@crm_required
def deal_delete(request, pk):
    deal = get_object_or_404(Deal, pk=pk)
    if request.method == 'POST':
        deal.delete()
        messages.success(request, 'Deal deleted.')
        return redirect('deal_pipeline')
    return render(request, 'deals/confirm_delete.html', {'deal': deal, 'page': 'deals'})
