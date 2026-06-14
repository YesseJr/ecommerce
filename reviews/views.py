from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from bookings.models import Booking
from properties.models import Property
from .models import Review
from .forms import ReviewForm


@login_required
def add_review(request, booking_reference):
    if not request.user.is_traveller:
        messages.error(request, "Only travellers can leave reviews.")
        return redirect('properties:home')

    booking = get_object_or_404(
        Booking,
        reference=booking_reference,
        traveller=request.user,
        status='confirmed'
    )

    # Check if review already exists
    if hasattr(booking, 'review'):
        messages.info(request, "You've already reviewed this stay.")
        return redirect('payments:confirmation', reference=booking_reference)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.booking   = booking
            review.traveller = request.user
            review.property  = booking.booking_property
            review.save()

            messages.success(
                request,
                "Thank you for your review! 🌟 It helps other travellers."
            )
            return redirect('properties:detail', slug=booking.booking_property.slug)
    else:
        form = ReviewForm()

    return render(request, 'reviews/add_review.html', {
        'form':    form,
        'booking': booking,
    })


@login_required
def delete_review(request, pk):
    review = get_object_or_404(Review, pk=pk, traveller=request.user)
    slug   = review.property.slug
    if request.method == 'POST':
        review.delete()
        messages.success(request, "Review deleted.")
    return redirect('properties:detail', slug=slug)