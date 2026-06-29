from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('search/', views.global_search, name='global_search'),
    path('cashier/stats/', views.cashier_live_stats, name='cashier_live_stats'),
]
