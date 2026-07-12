from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, LoginActivity


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = [
        'avatar', 'username', 'full_name',
        'email', 'role_badge', 'is_verified',
        'is_active', 'created_at'
    ]
    list_filter  = ['role', 'is_verified', 'is_active', 'is_superuser']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering     = ['-created_at']
    list_editable = ['is_verified', 'is_active']

    fieldsets = UserAdmin.fieldsets + (
        ('BookMyStay Info', {
            'fields': (
                'role', 'phone', 'profile_photo',
                'bio', 'location', 'is_verified'
            )
        }),
    )

    def avatar(self, obj):
        if obj.profile_photo:
            return format_html(
                '<img src="{}" style="width:35px; height:35px; border-radius:50%; object-fit:cover;"/>',
                obj.profile_photo.url
            )
        initial = (obj.first_name[0] if obj.first_name else obj.username[0]).upper()
        return format_html(
            '<div style="width:35px; height:35px; border-radius:50%; background:#1B3A6B; '
            'display:flex; align-items:center; justify-content:center; '
            'color:white; font-weight:bold; font-size:14px;">{}</div>',
            initial
        )
    avatar.short_description = ''

    def full_name(self, obj):
        return obj.get_full_name() or '—'
    full_name.short_description = 'Name'

    def role_badge(self, obj):
        colors = {
            'traveller': ('#FFF7ED', '#C2410C'),
            'owner':     ('#EFF6FF', '#1D4ED8'),
            'admin':     ('#F0FDF4', '#15803D'),
        }
        role = 'admin' if obj.is_superuser else obj.role
        bg, text = colors.get(role, ('#F3F4F6', '#374151'))
        return format_html(
            '<span style="background:{}; color:{}; padding:3px 10px; '
            'border-radius:999px; font-size:11px; font-weight:700;">{}</span>',
            bg, text,
            '⚙️ Admin' if role == 'admin' else
            '🏠 Owner' if role == 'owner' else
            '🧳 Traveller'
        )
    role_badge.short_description = 'Role'

@admin.register(LoginActivity)
class LoginActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'username_attempted', 'ip_address', 'success', 'created_at']
    list_filter = ['success', 'created_at']
    search_fields = ['user__username', 'username_attempted', 'ip_address']
    readonly_fields = [f.name for f in LoginActivity._meta.fields]

    def has_add_permission(self, request):
        return False
