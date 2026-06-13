from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<slug:slug>/', views.add_to_cart, name='add_to_cart'),
    path('cart/extras/add/<int:extra_pk>/', views.add_extra_to_cart, name='add_extra'),
    path('cart/extras/remove/<int:extra_pk>/', views.remove_extra_from_cart, name='remove_extra'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
]