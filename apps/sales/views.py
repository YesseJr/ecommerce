import re
from django.shortcuts import render, get_object_or_404, redirect
from apps.accounts.decorators import sales_required
from django.contrib import messages
from django.db.models import Sum
from django.http import JsonResponse
from decimal import Decimal, InvalidOperation
from .models import Sale, SaleItem
from apps.inventory.models import Fragrance
from apps.contacts.models import Contact


@sales_required
def sale_list(request):
    qs = Sale.objects.select_related('contact', 'cashier').order_by('-created_at')
    total_revenue = qs.filter(status='completed').aggregate(t=Sum('total'))['t'] or 0
    return render(request, 'sales/list.html', {
        'sales': qs[:50], 'total_revenue': total_revenue, 'page': 'sales'
    })


@sales_required
def sale_detail(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    return render(request, 'sales/detail.html', {'sale': sale, 'page': 'sales'})


def _safe_decimal(val, default='0'):
    try:
        return Decimal(str(val).strip() or default)
    except (InvalidOperation, TypeError):
        return Decimal(default)


@sales_required
def pos(request):
    fragrances = Fragrance.objects.filter(is_active=True, stock_quantity__gt=0).order_by('name')
    contacts   = Contact.objects.order_by('first_name', 'last_name')
    is_ajax    = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'cash')
        contact_id     = request.POST.get('contact') or None
        subtotal       = _safe_decimal(request.POST.get('subtotal'))
        discount       = _safe_decimal(request.POST.get('discount'))
        tendered       = _safe_decimal(request.POST.get('tendered'))
        total          = max(subtotal - discount, Decimal('0'))
        change         = max(tendered - total, Decimal('0')) if payment_method == 'cash' else Decimal('0')

        # Parse cart items from hidden inputs: items[0][id], items[0][qty], items[0][price]
        items = {}
        for key, val in request.POST.items():
            m = re.match(r'items\[(\d+)\]\[(\w+)\]', key)
            if m:
                idx, field = m.group(1), m.group(2)
                items.setdefault(idx, {})[field] = val

        if not items:
            err = 'Cart is empty — add items before completing the sale.'
            if is_ajax:
                return JsonResponse({'success': False, 'error': err}, status=400)
            messages.error(request, err)
            return redirect('pos')

        contact = Contact.objects.filter(pk=contact_id).first() if contact_id else None

        sale = Sale.objects.create(
            contact=contact,
            cashier=request.user,
            payment_method=payment_method,
            subtotal=subtotal,
            discount=discount,
            total=total,
            status='completed',
        )

        for idx, item in items.items():
            frag_id = item.get('id')
            qty     = max(int(item.get('qty', 1)), 1)
            price   = _safe_decimal(item.get('price'))
            try:
                frag = Fragrance.objects.get(pk=frag_id, is_active=True)
                actual_qty = min(qty, frag.stock_quantity)   # never over-sell
                if actual_qty <= 0:
                    continue
                SaleItem.objects.create(
                    sale=sale, fragrance=frag,
                    quantity=actual_qty,
                    unit_price=price,
                    total_price=price * actual_qty,
                )
                frag.stock_quantity = max(0, frag.stock_quantity - actual_qty)
                frag.save(update_fields=['stock_quantity'])

                if contact:
                    pts = int((price * actual_qty) / 1000)
                    if pts:
                        contact.loyalty_points += pts
                        contact.save(update_fields=['loyalty_points'])
            except Fragrance.DoesNotExist:
                pass

        if is_ajax:
            return JsonResponse({
                'success':    True,
                'reference':  sale.reference,
                'total':      float(total),
                'change':     float(change),
                'payment':    sale.get_payment_method_display(),
                'customer':   contact.full_name if contact else 'Walk-in',
                'redirect':   f'/sales/{sale.pk}/',
            })

        messages.success(request, f'Sale {sale.reference} completed — TZS {total:,.0f}')
        return redirect('sale_detail', pk=sale.pk)

    return render(request, 'sales/pos.html', {
        'fragrances': fragrances,
        'contacts': contacts,
        'page': 'pos',
    })
