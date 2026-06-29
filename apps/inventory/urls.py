from django.urls import path
from . import views
urlpatterns = [
    path('', views.fragrance_list, name='fragrance_list'),
    path('new/', views.fragrance_create, name='fragrance_create'),
    path('<int:pk>/edit/', views.fragrance_update, name='fragrance_update'),
    path('<int:pk>/delete/', views.fragrance_delete, name='fragrance_delete'),
]
