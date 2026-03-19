from django.contrib import admin
from .models import QuizAttempt, AttemptAnswer


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display  = ['user', 'quiz', 'status', 'score',
                     'percentage', 'is_passed', 'started_at']
    list_filter   = ['status', 'is_passed']
    search_fields = ['user__email', 'quiz__title']
    ordering      = ['-started_at']


@admin.register(AttemptAnswer)
class AttemptAnswerAdmin(admin.ModelAdmin):
    list_display  = ['attempt', 'question', 'selected_choice',
                     'is_correct', 'marks_awarded']
    list_filter   = ['is_correct']