from django.urls import path
from . import views
urlpatterns = [
    path('', views.sale_list, name='sale_list'),
    path('pos/', views.pos, name='pos'),
    path('<int:pk>/', views.sale_detail, name='sale_detail'),
]
