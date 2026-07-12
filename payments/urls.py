from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('checkout/',                    views.checkout,         name='checkout'),
    path('coupon/apply/',                views.apply_coupon,     name='apply_coupon'),
    path('coupon/remove/',               views.remove_coupon,    name='remove_coupon'),
    path('process/',                     views.process_payment,  name='process_payment'),
    path('confirmation/<str:reference>/', views.confirmation,    name='confirmation'),
    path('my-bookings/',                 views.my_bookings,      name='my_bookings'),
    path('history/',                     views.payment_history,  name='payment_history'),
    path('cancel/<str:reference>/',      views.cancel_booking,   name='cancel_booking'),
    path('set-currency/',                views.set_currency,     name='set_currency'),
    path('currency-info/',               views.currency_info,    name='currency_info'),
]
