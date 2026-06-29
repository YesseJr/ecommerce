from django.shortcuts import render, get_object_or_404, redirect
from apps.accounts.decorators import crm_required, contacts_view_edit
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from .models import Contact
from .forms import ContactForm


@contacts_view_edit
def contact_list(request):
    qs = Contact.objects.all()
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')
    if q:
        qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(phone__icontains=q) | Q(email__icontains=q))
    if status:
        qs = qs.filter(status=status)
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'contacts/list.html', {
        'page_obj': page_obj, 'q': q, 'status_filter': status,
        'total': Contact.objects.count(),
        'page': 'contacts',
    })


@contacts_view_edit
def contact_detail(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    sales = contact.sale_set.order_by('-created_at')[:10]
    deals = contact.deals.order_by('-created_at')[:5]
    return render(request, 'contacts/detail.html', {
        'contact': contact, 'sales': sales, 'deals': deals, 'page': 'contacts'
    })


@crm_required
def contact_create(request):
    form = ContactForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        contact = form.save(commit=False)
        contact.created_by = request.user
        contact.save()
        messages.success(request, f'{contact.full_name} added successfully.')
        return redirect('contact_detail', pk=contact.pk)
    return render(request, 'contacts/form.html', {'form': form, 'title': 'Add contact', 'page': 'contacts'})


@contacts_view_edit
def contact_update(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    form = ContactForm(request.POST or None, instance=contact)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Contact updated.')
        return redirect('contact_detail', pk=contact.pk)
    return render(request, 'contacts/form.html', {'form': form, 'contact': contact, 'title': 'Edit contact', 'page': 'contacts'})


@crm_required
def contact_delete(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    if request.method == 'POST':
        name = contact.full_name
        contact.delete()
        messages.success(request, f'{name} deleted.')
        return redirect('contact_list')
    return render(request, 'contacts/confirm_delete.html', {'contact': contact, 'page': 'contacts'})
