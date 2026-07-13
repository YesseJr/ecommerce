from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    path('', views.hub, name='hub'),

    # Moderator
    path('moderator/', views.moderator_dashboard, name='moderator'),
    path('moderator/property/<slug:slug>/<str:action>/', views.moderate_property, name='moderate_property'),
    path('moderator/review/<int:pk>/<str:action>/', views.moderate_review, name='moderate_review'),

    # Support
    path('support/', views.support_dashboard, name='support'),
    path('support/conversation/<int:pk>/', views.support_conversation_view, name='support_conversation'),

    # Finance
    path('finance/', views.finance_dashboard, name='finance'),
]
