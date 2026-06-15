from django.shortcuts import render


def error_404(request, exception):
    return render(request, '404.html', status=404)


def error_500(request):
    return render(request, '500.html', status=500)
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# ✅ Custom error handlers
handler404 = 'bookmystay.views.error_404'
handler500 = 'bookmystay.views.error_500'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('properties.urls')),
    path('users/', include('users.urls')),
    path('bookings/', include('bookings.urls')),
    path('payments/', include('payments.urls')),
    path('reviews/', include('reviews.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)