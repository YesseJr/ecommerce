from django.urls import path
from . import views
urlpatterns = [
    path('', views.company_list, name='company_list'),
    path('new/', views.company_create, name='company_create'),
    path('<int:pk>/edit/', views.company_update, name='company_update'),
    path('<int:pk>/delete/', views.company_delete, name='company_delete'),
]
