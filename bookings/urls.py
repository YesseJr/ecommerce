from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<slug:slug>/', views.add_to_cart, name='add_to_cart'),
    path('cart/extras/sync/', views.sync_cart_extras, name='sync_extras'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('cart/notes/', views.update_cart_notes, name='update_cart_notes'),
    path('cron/send-stay-emails/<str:secret>/', views.cron_send_stay_emails, name='cron_send_stay_emails'),
]