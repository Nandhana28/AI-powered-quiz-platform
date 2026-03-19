from django.contrib import admin
from .models import Badge, UserBadge, UserGameProfile, PersonalBest, UserTopicStat


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display  = ['name', 'condition_type', 'is_active', 'created_at']
    list_filter   = ['condition_type', 'is_active']
    search_fields = ['name']


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display  = ['user', 'badge', 'earned_at']
    search_fields = ['user__email', 'badge__name']


@admin.register(UserGameProfile)
class UserGameProfileAdmin(admin.ModelAdmin):
    list_display  = ['user', 'level', 'xp_total', 'streak_easy',
                     'streak_medium', 'streak_hard']
    search_fields = ['user__email']
    list_filter   = ['level']


@admin.register(PersonalBest)
class PersonalBestAdmin(admin.ModelAdmin):
    list_display  = ['user', 'topic', 'difficulty', 'best_score', 'achieved_at']
    list_filter   = ['difficulty']
    search_fields = ['user__email', 'topic__name']


@admin.register(UserTopicStat)
class UserTopicStatAdmin(admin.ModelAdmin):
    list_display  = ['user', 'topic', 'total_attempts',
                     'avg_score', 'best_score', 'last_attempted_at']
    search_fields = ['user__email', 'topic__name']