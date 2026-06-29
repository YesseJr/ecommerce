from django.shortcuts import render, get_object_or_404, redirect
from apps.accounts.decorators import crm_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Lead
from .forms import LeadForm

@crm_required
def lead_list(request):
    qs = Lead.objects.select_related('contact', 'assigned_to')
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(email__icontains=q) | Q(contact__first_name__icontains=q))
    if status:
        qs = qs.filter(status=status)
    page_obj = Paginator(qs, 20).get_page(request.GET.get('page'))
    return render(request, 'leads/list.html', {'page_obj': page_obj, 'q': q, 'status_filter': status, 'page': 'leads'})

@crm_required
def lead_create(request):
    form = LeadForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        lead = form.save(commit=False)
        lead.created_by = request.user
        lead.save()
        messages.success(request, 'Lead added.')
        return redirect('lead_list')
    return render(request, 'leads/form.html', {'form': form, 'title': 'New lead', 'page': 'leads'})

@crm_required
def lead_update(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    form = LeadForm(request.POST or None, instance=lead)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Lead updated.')
        return redirect('lead_list')
    return render(request, 'leads/form.html', {'form': form, 'lead': lead, 'title': 'Edit lead', 'page': 'leads'})

@crm_required
def lead_delete(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == 'POST':
        lead.delete()
        messages.success(request, 'Lead deleted.')
        return redirect('lead_list')
    return render(request, 'leads/confirm_delete.html', {'lead': lead, 'page': 'leads'})
