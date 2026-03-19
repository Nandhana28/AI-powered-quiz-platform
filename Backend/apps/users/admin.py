from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile, PasswordResetToken, UserLoginHistory


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display  = ['email', 'username', 'role', 'is_active', 'created_at']
    list_filter   = ['role', 'is_active']
    search_fields = ['email', 'username']
    ordering      = ['-created_at']
    fieldsets     = UserAdmin.fieldsets + (
        ('Role', {'fields': ('role',)}),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display  = ['user', 'display_name', 'is_deleted', 'created_at']
    search_fields = ['user__email', 'display_name']


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display  = ['user', 'token', 'is_used', 'expires_at', 'created_at']
    list_filter   = ['is_used']
    search_fields = ['user__email']


@admin.register(UserLoginHistory)
class UserLoginHistoryAdmin(admin.ModelAdmin):
    list_display  = ['email_attempted', 'status', 'ip_address', 'created_at']
    list_filter   = ['status']
    search_fields = ['email_attempted']