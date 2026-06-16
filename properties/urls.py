from django.urls import path
from . import views

app_name = 'properties'

urlpatterns = [
    # Public
    path('', views.home, name='home'),
    path('properties/', views.property_list, name='list'),
    path('properties/<slug:slug>/', views.property_detail, name='detail'),

    # Owner
    path('dashboard/', views.owner_dashboard, name='owner_dashboard'),
    path('dashboard/add/', views.add_property, name='add_property'),
    path('dashboard/edit/<slug:slug>/', views.edit_property, name='edit_property'),
    path('dashboard/delete/<slug:slug>/', views.delete_property, name='delete_property'),
    path('dashboard/extras/<slug:slug>/', views.manage_extras, name='manage_extras'),
    path('dashboard/extras/delete/<int:pk>/', views.delete_extra, name='delete_extra'),
    path('dashboard/bookings/', views.owner_bookings, name='owner_bookings'),
    path('dashboard/images/delete/<int:pk>/', views.delete_image, name='delete_image'),
    path('dashboard/images/set-primary/<int:pk>/', views.set_primary_image, name='set_primary_image'),
]