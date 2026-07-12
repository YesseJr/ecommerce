from django.urls import path
from . import views

app_name = 'inbox'

urlpatterns = [
    path('', views.inbox_view, name='inbox'),
    path('<int:pk>/', views.conversation_thread, name='thread'),
    path('start/<slug:slug>/', views.start_conversation, name='start'),
    path('notifications/dropdown/', views.notifications_dropdown, name='notifications_dropdown'),
    path('notifications/mark-read/', views.mark_notifications_read, name='mark_notifications_read'),
]
