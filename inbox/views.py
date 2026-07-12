from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages as flash
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Conversation, Message, Notification
from properties.models import Property


@login_required
def inbox_view(request):
    """List every conversation this user is part of, as guest or host."""
    conversations = Conversation.objects.filter(
        models_q_for(request.user)
    ).select_related('property', 'guest', 'host').order_by('-updated_at')

    for c in conversations:
        c.other = c.other_party(request.user)
        c.unread = c.unread_count_for(request.user)

    return render(request, 'inbox/inbox.html', {
        'conversations': conversations,
    })


def models_q_for(user):
    from django.db.models import Q
    return Q(guest=user) | Q(host=user)


@login_required
def conversation_thread(request, pk):
    convo = get_object_or_404(
        Conversation.objects.select_related('property', 'guest', 'host'), pk=pk
    )
    if request.user not in (convo.guest, convo.host):
        flash.error(request, "You don't have access to that conversation.")
        return redirect('inbox:inbox')

    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            Message.objects.create(conversation=convo, sender=request.user, body=body)
            convo.save()  # bumps updated_at (auto_now) so the inbox list re-sorts
            other = convo.other_party(request.user)
            Notification.send(
                other,
                title=f"New message from {request.user.first_name or request.user.username}",
                body=body[:100],
                link=f'/inbox/{convo.pk}/',
                notif_type='message',
            )
        return redirect('inbox:thread', pk=convo.pk)

    # Mark incoming messages as read
    convo.messages.exclude(sender=request.user).update(is_read=True)

    return render(request, 'inbox/thread.html', {
        'convo': convo,
        'other': convo.other_party(request.user),
        'thread_messages': convo.messages.select_related('sender'),
    })


@login_required
def start_conversation(request, slug):
    prop = get_object_or_404(Property, slug=slug, status='active')
    if request.user == prop.owner:
        flash.error(request, "You can't message yourself about your own listing.")
        return redirect('properties:detail', slug=slug)

    convo, created = Conversation.objects.get_or_create(
        property=prop, guest=request.user, defaults={'host': prop.owner}
    )

    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            Message.objects.create(conversation=convo, sender=request.user, body=body)
            Notification.send(
                prop.owner,
                title=f"New inquiry about {prop.name}",
                body=body[:100],
                link=f'/inbox/{convo.pk}/',
                notif_type='message',
            )
            flash.success(request, "Message sent to the host.")

    return redirect('inbox:thread', pk=convo.pk)


@login_required
def notifications_dropdown(request):
    """AJAX endpoint — powers the bell icon dropdown in the navbar."""
    notes = request.user.notifications.all()[:8]
    unread = request.user.notifications.filter(is_read=False).count()
    return render(request, 'inbox/_notifications_dropdown.html', {
        'notes': notes,
        'unread': unread,
    })


@login_required
@require_POST
def mark_notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return JsonResponse({'ok': True})
