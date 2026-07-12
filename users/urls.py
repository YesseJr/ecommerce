from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    # Email verification — specific paths MUST come before the dynamic
    # <str:token> pattern, or it greedily swallows "resend"/"resend-public"
    # as if they were tokens.
    path('verify/resend/', views.resend_verification, name='resend_verification'),
    path('verify/resend-public/', views.resend_verification_public, name='resend_verification_public'),
    path('verify/<str:token>/', views.verify_email, name='verify_email'),

    # Login activity
    path('login-activity/', views.login_activity_view, name='login_activity'),

    # Password reset (Django's built-in flow, custom templates)
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='users/password_reset.html',
        email_template_name='users/email/password_reset_email.txt',
        html_email_template_name='users/email/password_reset_email.html',
        subject_template_name='users/email/password_reset_subject.txt',
        success_url='/users/password-reset/sent/',
    ), name='password_reset'),
    path('password-reset/sent/', auth_views.PasswordResetDoneView.as_view(
        template_name='users/password_reset_sent.html'
    ), name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='users/password_reset_confirm.html',
        success_url='/users/password-reset/complete/',
    ), name='password_reset_confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='users/password_reset_complete.html'
    ), name='password_reset_complete'),
]