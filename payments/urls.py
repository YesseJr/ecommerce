from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('process/', views.process_payment, name='process_payment'),
    path('confirmation/<str:reference>/', views.confirmation, name='confirmation'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
]