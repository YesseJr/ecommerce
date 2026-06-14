from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('add/<str:booking_reference>/', views.add_review, name='add_review'),
    path('delete/<int:pk>/', views.delete_review, name='delete_review'),
]