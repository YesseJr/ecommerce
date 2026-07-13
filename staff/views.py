from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.core.paginator import Paginator

from .decorators import staff_role_required
from properties.models import Property
from reviews.models import Review
from bookings.models import Booking
from payments.models import Payment, Coupon
from inbox.models import Conversation


@login_required
def hub(request):
    """Landing page listing whichever staff dashboards this user can reach."""
    user = request.user
    if not user.is_staff_role:
        messages.error(request, "You don't have access to the staff area.")
        return redirect('properties:home')

    tiles = []
    if user.is_moderator:
        tiles.append({
            'title': 'Moderator', 'url': 'staff:moderator',
            'desc': 'Review pending listings and moderate reviews.',
            'icon': 'shield-check',
            'count': Property.objects.filter(status='pending').count(),
        })
    if user.is_support:
        tiles.append({
            'title': 'Support', 'url': 'staff:support',
            'desc': 'Look up bookings and guest-host conversations.',
            'icon': 'life-buoy',
            'count': None,
        })
    if user.is_finance:
        tiles.append({
            'title': 'Finance', 'url': 'staff:finance',
            'desc': 'Revenue, payments, refunds, and coupon usage.',
            'icon': 'landmark',
            'count': None,
        })
    if user.is_admin:
        tiles.append({
            'title': 'Django Admin', 'url': None, 'href': '/admin/',
            'desc': 'Full administrative control.',
            'icon': 'settings',
            'count': None,
        })

    return render(request, 'staff/hub.html', {'tiles': tiles})


# ─── MODERATOR ──────────────────────────────────────────────────────────────

@staff_role_required('is_moderator')
def moderator_dashboard(request):
    pending_properties = Property.objects.filter(status='pending').order_by('created_at')
    flagged_reviews = Review.objects.filter(is_hidden=False).select_related('traveller', 'property').order_by('-created_at')[:20]
    hidden_reviews = Review.objects.filter(is_hidden=True).select_related('traveller', 'property', 'moderated_by').order_by('-moderated_at')[:10]

    return render(request, 'staff/moderator_dashboard.html', {
        'pending_properties': pending_properties,
        'flagged_reviews': flagged_reviews,
        'hidden_reviews': hidden_reviews,
    })


@staff_role_required('is_moderator')
def moderate_property(request, slug, action):
    prop = get_object_or_404(Property, slug=slug)
    if request.method != 'POST':
        return redirect('staff:moderator')

    if action == 'approve':
        prop.status = 'active'
        prop.save(update_fields=['status'])
        messages.success(request, f'"{prop.name}" approved and is now live.')
    elif action == 'reject':
        prop.status = 'inactive'
        prop.save(update_fields=['status'])
        messages.warning(request, f'"{prop.name}" rejected and set to inactive.')
    else:
        messages.error(request, "Unknown moderation action.")

    return redirect('staff:moderator')


@staff_role_required('is_moderator')
def moderate_review(request, pk, action):
    review = get_object_or_404(Review, pk=pk)
    if request.method != 'POST':
        return redirect('staff:moderator')

    if action == 'hide':
        review.is_hidden = True
        review.hidden_reason = request.POST.get('reason', '').strip()
        review.moderated_by = request.user
        review.moderated_at = timezone.now()
        review.save(update_fields=['is_hidden', 'hidden_reason', 'moderated_by', 'moderated_at'])
        messages.success(request, "Review hidden from public view.")
    elif action == 'unhide':
        review.is_hidden = False
        review.hidden_reason = ''
        review.moderated_by = request.user
        review.moderated_at = timezone.now()
        review.save(update_fields=['is_hidden', 'hidden_reason', 'moderated_by', 'moderated_at'])
        messages.success(request, "Review restored to public view.")
    else:
        messages.error(request, "Unknown moderation action.")

    return redirect('staff:moderator')


# ─── SUPPORT ────────────────────────────────────────────────────────────────

@staff_role_required('is_support')
def support_dashboard(request):
    query = request.GET.get('q', '').strip()

    bookings = Booking.objects.select_related('traveller', 'booking_property').order_by('-created_at')
    conversations = Conversation.objects.select_related('property', 'guest', 'host').order_by('-updated_at')

    if query:
        bookings = bookings.filter(
            Q(reference__icontains=query) |
            Q(traveller__username__icontains=query) |
            Q(traveller__email__icontains=query) |
            Q(booking_property__name__icontains=query)
        )
        conversations = conversations.filter(
            Q(guest__username__icontains=query) |
            Q(host__username__icontains=query) |
            Q(property__name__icontains=query)
        )

    booking_page = Paginator(bookings, 15).get_page(request.GET.get('page'))

    return render(request, 'staff/support_dashboard.html', {
        'bookings': booking_page,
        'conversations': conversations[:15],
        'query': query,
    })


@staff_role_required('is_support')
def support_conversation_view(request, pk):
    """Read-only view into a conversation — support can see context to help
    resolve an issue without inserting themselves into the guest/host thread."""
    convo = get_object_or_404(Conversation.objects.select_related('property', 'guest', 'host'), pk=pk)
    thread_messages = convo.messages.select_related('sender').order_by('created_at')
    return render(request, 'staff/support_conversation.html', {
        'convo': convo,
        'thread_messages': thread_messages,
    })


# ─── FINANCE ────────────────────────────────────────────────────────────────

@staff_role_required('is_finance')
def finance_dashboard(request):
    confirmed = Booking.objects.filter(status='confirmed')
    cancelled = Booking.objects.filter(status='cancelled')

    total_revenue   = confirmed.aggregate(s=Sum('grand_total'))['s'] or 0
    total_fees      = confirmed.aggregate(s=Sum('service_fee'))['s'] or 0
    total_tax       = confirmed.aggregate(s=Sum('tax_amount'))['s'] or 0
    total_discounts = confirmed.aggregate(s=Sum('discount_amount'))['s'] or 0
    total_refunded  = cancelled.aggregate(s=Sum('refund_amount'))['s'] or 0

    recent_payments = Payment.objects.select_related('booking', 'booking__traveller').order_by('-created_at')[:20]
    coupons = Coupon.objects.order_by('-created_at')[:15]

    payment_status_counts = Payment.objects.values('status').annotate(count=Count('id'))

    return render(request, 'staff/finance_dashboard.html', {
        'total_revenue':   total_revenue,
        'total_fees':      total_fees,
        'total_tax':       total_tax,
        'total_discounts': total_discounts,
        'total_refunded':  total_refunded,
        'confirmed_count': confirmed.count(),
        'cancelled_count': cancelled.count(),
        'recent_payments': recent_payments,
        'coupons':         coupons,
        'payment_status_counts': payment_status_counts,
    })
