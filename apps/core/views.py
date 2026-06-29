import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count, Q, Avg


def _tz_day_range(d):
    """Return (start, end) as tz-aware datetimes for a given date, in Africa/Dar_es_Salaam."""
    return (
        timezone.make_aware(datetime.datetime.combine(d, datetime.time.min)),
        timezone.make_aware(datetime.datetime.combine(d, datetime.time.max)),
    )


@login_required
def dashboard(request):
    from apps.contacts.models import Contact
    from apps.deals.models import Deal
    from apps.inventory.models import Fragrance
    from apps.sales.models import Sale, SaleItem
    from apps.expenses.models import Expense

    now      = timezone.now()
    today    = timezone.localdate()                                    # date in Africa/Dar_es_Salaam
    week_start = today - timedelta(days=today.weekday())              # Monday

    month_start = timezone.make_aware(
        datetime.datetime(today.year, today.month, 1)
    )
    last_month_dt = month_start - timedelta(days=1)
    last_month_start = timezone.make_aware(
        datetime.datetime(last_month_dt.year, last_month_dt.month, 1)
    )

    today_start, today_end   = _tz_day_range(today)
    week_start_dt            = timezone.make_aware(datetime.datetime.combine(week_start, datetime.time.min))

    # Revenue this month & last (global, for admin / manager)
    rev_this = Sale.objects.filter(
        status='completed', created_at__gte=month_start
    ).aggregate(t=Sum('total'))['t'] or 0

    rev_last = Sale.objects.filter(
        status='completed',
        created_at__gte=last_month_start,
        created_at__lt=month_start,
    ).aggregate(t=Sum('total'))['t'] or 0

    rev_change = round(((float(rev_this) - float(rev_last)) / float(rev_last)) * 100, 1) if rev_last else 0

    # Low stock
    all_frags    = list(Fragrance.objects.filter(is_active=True))
    low_items    = [f for f in all_frags if f.is_low_stock]
    low_stock_count = len(low_items)

    # 6-month revenue chart (shared)
    chart_data = []
    for i in range(5, -1, -1):
        ref   = today.replace(day=1) - timedelta(days=30 * i)
        ms    = timezone.make_aware(datetime.datetime(ref.year, ref.month, 1))
        nxt   = ref.replace(day=28) + timedelta(days=4)
        me_dt = timezone.make_aware(datetime.datetime(nxt.year, nxt.month, 1))
        t = Sale.objects.filter(
            status='completed', created_at__gte=ms, created_at__lt=me_dt
        ).aggregate(t=Sum('total'))['t'] or 0
        chart_data.append({'month': ms.strftime('%b'), 'total': float(t)})

    role = getattr(request.user, 'role', '')

    # ────────────────────────────────────────────────
    #  ADMIN DASHBOARD
    # ────────────────────────────────────────────────
    if role == 'admin' or request.user.is_superuser:
        expenses_this = Expense.objects.filter(
            date__gte=today.replace(day=1), date__lte=today
        ).aggregate(t=Sum('amount'))['t'] or 0
        profit_this = float(rev_this) - float(expenses_this)

        total_contacts = Contact.objects.count()
        new_this_week  = Contact.objects.filter(created_at__gte=week_start_dt).count()

        active_deals   = Deal.objects.filter(stage__in=['lead', 'qualified', 'proposal', 'negotiation'])
        pipeline_value = active_deals.aggregate(t=Sum('value'))['t'] or 0
        open_deals     = active_deals.count()

        deal_stages = []
        for stage, label in Deal.STAGE_CHOICES:
            qs = Deal.objects.filter(stage=stage)
            deal_stages.append({
                'stage': stage, 'label': label,
                'count': qs.count(),
                'total': float(qs.aggregate(t=Sum('value'))['t'] or 0),
            })

        top_contacts = Contact.objects.annotate(
            ltv=Sum('sale__total', filter=Q(sale__status='completed'))
        ).order_by('-ltv')[:5]

        recent_sales = Sale.objects.select_related('contact', 'cashier').order_by('-created_at')[:8]

        expense_cats = Expense.objects.filter(
            date__gte=today.replace(day=1), date__lte=today
        ).values('category').annotate(total=Sum('amount')).order_by('-total')[:5]

        context = {
            'rev_this': rev_this, 'rev_last': rev_last, 'rev_change': rev_change,
            'expenses_this': expenses_this, 'profit_this': profit_this,
            'total_contacts': total_contacts, 'new_this_week': new_this_week,
            'pipeline_value': pipeline_value, 'open_deals': open_deals,
            'low_stock_count': low_stock_count, 'low_stock_items': low_items[:5],
            'chart_data': chart_data,
            'deal_stages': deal_stages,
            'top_contacts': top_contacts,
            'recent_sales': recent_sales,
            'expense_cats': expense_cats,
            'page': 'dashboard',
        }
        return render(request, 'dashboard/admin.html', context)

    # ────────────────────────────────────────────────
    #  MANAGER DASHBOARD
    # ────────────────────────────────────────────────
    elif role == 'manager':
        sales_count_this = Sale.objects.filter(status='completed', created_at__gte=month_start).count()
        avg_sale         = round(float(rev_this) / sales_count_this, 0) if sales_count_this else 0
        active_contacts  = Contact.objects.filter(status__in=['active', 'vip']).count()

        pending_deals = Deal.objects.filter(
            stage__in=['proposal', 'negotiation']
        ).select_related('contact').order_by('-value')[:6]

        top_contacts = Contact.objects.annotate(
            ltv=Sum('sale__total', filter=Q(sale__status='completed'))
        ).order_by('-ltv')[:5]

        recent_sales = Sale.objects.select_related('contact', 'cashier').order_by('-created_at')[:10]

        cashier_stats = Sale.objects.filter(
            status='completed', created_at__gte=month_start
        ).values(
            'cashier__first_name', 'cashier__last_name', 'cashier__username'
        ).annotate(sales_count=Count('id'), revenue=Sum('total')).order_by('-revenue')[:5]

        context = {
            'rev_this': rev_this, 'rev_last': rev_last, 'rev_change': rev_change,
            'sales_count_this': sales_count_this, 'avg_sale': avg_sale,
            'active_contacts': active_contacts,
            'low_stock_count': low_stock_count, 'low_stock_items': low_items[:5],
            'chart_data': chart_data,
            'pending_deals': pending_deals,
            'top_contacts': top_contacts,
            'recent_sales': recent_sales,
            'cashier_stats': cashier_stats,
            'page': 'dashboard',
        }
        return render(request, 'dashboard/manager.html', context)

    # ────────────────────────────────────────────────
    #  CASHIER DASHBOARD
    # ────────────────────────────────────────────────
    else:
        me = request.user

        # ── Reliable tz-aware date ranges ──
        my_today_qs = Sale.objects.filter(
            cashier=me,
            created_at__gte=today_start,
            created_at__lte=today_end,
        )
        my_week_qs = Sale.objects.filter(
            cashier=me,
            created_at__gte=week_start_dt,
        )
        my_month_qs = Sale.objects.filter(
            cashier=me,
            created_at__gte=month_start,
        )

        # Today
        my_sales_today_count = my_today_qs.count()
        my_sales_today_rev   = my_today_qs.filter(status='completed').aggregate(t=Sum('total'))['t'] or 0
        my_discount_today    = my_today_qs.filter(status='completed').aggregate(t=Sum('discount'))['t'] or 0

        # Avg sale value today
        my_avg_today = (
            round(float(my_sales_today_rev) / my_sales_today_count, 0)
            if my_sales_today_count else 0
        )

        # This week
        my_sales_week_count = my_week_qs.count()
        my_sales_week_rev   = my_week_qs.filter(status='completed').aggregate(t=Sum('total'))['t'] or 0

        # This month
        my_sales_month_rev   = my_month_qs.filter(status='completed').aggregate(t=Sum('total'))['t'] or 0
        my_sales_month_count = my_month_qs.filter(status='completed').count()

        # Items sold today (sum of quantities across all my sales today)
        from apps.sales.models import SaleItem
        my_items_today = SaleItem.objects.filter(
            sale__cashier=me,
            sale__created_at__gte=today_start,
            sale__created_at__lte=today_end,
            sale__status='completed',
        ).aggregate(t=Sum('quantity'))['t'] or 0

        # Top-selling product today
        top_product_today = SaleItem.objects.filter(
            sale__cashier=me,
            sale__created_at__gte=today_start,
            sale__created_at__lte=today_end,
            sale__status='completed',
        ).values('fragrance__name').annotate(
            qty=Sum('quantity')
        ).order_by('-qty').first()

        my_recent_sales = Sale.objects.filter(
            cashier=me
        ).select_related('contact').order_by('-created_at')[:10]

        from apps.contacts.models import Contact
        my_top_contacts = Contact.objects.filter(
            sale__cashier=me, sale__status='completed'
        ).annotate(
            my_ltv=Sum('sale__total', filter=Q(sale__cashier=me, sale__status='completed'))
        ).order_by('-my_ltv')[:5]

        context = {
            # Today stats
            'my_sales_today_count': my_sales_today_count,
            'my_sales_today_rev':   my_sales_today_rev,
            'my_discount_today':    my_discount_today,
            'my_avg_today':         my_avg_today,
            'my_items_today':       my_items_today,
            'top_product_today':    top_product_today,
            # Week stats
            'my_sales_week_count':  my_sales_week_count,
            'my_sales_week_rev':    my_sales_week_rev,
            # Month stats
            'my_sales_month_rev':   my_sales_month_rev,
            'my_sales_month_count': my_sales_month_count,
            # Lists
            'my_recent_sales':      my_recent_sales,
            'my_top_contacts':      my_top_contacts,
            # Stock
            'low_stock_count':  low_stock_count,
            'low_stock_items':  low_items[:4],
            'page': 'dashboard',
        }
        return render(request, 'dashboard/cashier.html', context)


@login_required
def cashier_live_stats(request):
    """Lightweight JSON endpoint — cashier dashboard auto-refresh every 60 s."""
    from apps.sales.models import Sale, SaleItem

    me    = request.user
    today = timezone.localdate()
    today_start, today_end = _tz_day_range(today)
    week_start = today - timedelta(days=today.weekday())
    week_start_dt = timezone.make_aware(datetime.datetime.combine(week_start, datetime.time.min))

    today_qs = Sale.objects.filter(cashier=me, created_at__gte=today_start, created_at__lte=today_end)
    week_qs  = Sale.objects.filter(cashier=me, created_at__gte=week_start_dt)

    today_count = today_qs.count()
    today_rev   = float(today_qs.filter(status='completed').aggregate(t=Sum('total'))['t'] or 0)
    week_rev    = float(week_qs.filter(status='completed').aggregate(t=Sum('total'))['t'] or 0)
    items_today = SaleItem.objects.filter(
        sale__cashier=me,
        sale__created_at__gte=today_start,
        sale__created_at__lte=today_end,
        sale__status='completed',
    ).aggregate(t=Sum('quantity'))['t'] or 0

    avg_today = round(today_rev / today_count, 0) if today_count else 0

    return JsonResponse({
        'today_count': today_count,
        'today_rev':   today_rev,
        'week_rev':    week_rev,
        'items_today': items_today,
        'avg_today':   avg_today,
    })


@login_required
def global_search(request):
    q = request.GET.get('q', '').strip()
    if not q or len(q) < 2:
        return JsonResponse({'results': []})

    results = []
    role = getattr(request.user, 'role', '')
    is_admin_or_super = request.user.is_superuser or role == 'admin'
    has_crm      = is_admin_or_super or role == 'manager'
    has_contacts = has_crm or role == 'cashier'
    has_sales    = role in ('manager', 'cashier')

    if has_contacts:
        from apps.contacts.models import Contact
        for c in Contact.objects.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q)
        )[:4]:
            results.append({'type': 'Contact', 'name': c.full_name,
                            'sub': c.email or c.phone or '', 'url': f'/contacts/{c.pk}/'})

    if has_crm:
        from apps.leads.models import Lead
        from apps.deals.models import Deal
        from apps.inventory.models import Fragrance

        for l in Lead.objects.filter(Q(name__icontains=q) | Q(email__icontains=q))[:3]:
            results.append({'type': 'Lead', 'name': l.name,
                            'sub': l.get_status_display(), 'url': f'/leads/{l.pk}/edit/'})

        for d in Deal.objects.filter(Q(title__icontains=q))[:3]:
            results.append({'type': 'Deal', 'name': d.title,
                            'sub': d.get_stage_display(), 'url': f'/deals/{d.pk}/edit/'})

        for f in Fragrance.objects.filter(
            Q(name__icontains=q) | Q(brand__icontains=q) | Q(sku__icontains=q), is_active=True
        )[:3]:
            results.append({'type': 'Fragrance', 'name': f'{f.name} — {f.brand}',
                            'sub': f'TZS {f.price:,.0f} · {f.stock_quantity} in stock',
                            'url': f'/inventory/{f.pk}/edit/'})

    if has_sales:
        from apps.sales.models import Sale
        for s in Sale.objects.filter(Q(reference__icontains=q)).select_related('contact')[:4]:
            results.append({'type': 'Sale', 'name': s.reference,
                            'sub': f'TZS {s.total:,.0f} · {s.get_status_display()}',
                            'url': f'/sales/{s.pk}/'})

    return JsonResponse({'results': results[:10]})
