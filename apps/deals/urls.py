from django.urls import path
from . import views
urlpatterns = [
    path('', views.deal_pipeline, name='deal_pipeline'),
    path('list/', views.deal_list, name='deal_list'),
    path('new/', views.deal_create, name='deal_create'),
    path('<int:pk>/edit/', views.deal_update, name='deal_update'),
    path('<int:pk>/delete/', views.deal_delete, name='deal_delete'),
]
