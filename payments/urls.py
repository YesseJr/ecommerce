from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('checkout/',                    views.checkout,         name='checkout'),
    path('process/',                     views.process_payment,  name='process_payment'),
    path('confirmation/<str:reference>/', views.confirmation,    name='confirmation'),
    path('my-bookings/',                 views.my_bookings,      name='my_bookings'),
    path('history/',                     views.payment_history,  name='payment_history'),
    path('set-currency/',                views.set_currency,     name='set_currency'),
    path('currency-info/',               views.currency_info,    name='currency_info'),
]
