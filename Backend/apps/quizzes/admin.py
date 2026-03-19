from django.contrib import admin
from .models import Topic, Quiz, Question, Choice


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display  = ['name', 'parent', 'level', 'is_active', 'created_at']
    list_filter   = ['level', 'is_active']
    search_fields = ['name']
    ordering      = ['level', 'name']


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display  = ['title', 'topic', 'difficulty', 'is_published',
                     'is_ai_generated', 'is_deleted', 'created_at']
    list_filter   = ['difficulty', 'is_published', 'is_ai_generated', 'is_deleted']
    search_fields = ['title']
    ordering      = ['-created_at']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display  = ['text', 'quiz', 'order', 'marks', 'is_deleted']
    list_filter   = ['is_deleted']
    search_fields = ['text', 'quiz__title']


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display  = ['text', 'question', 'is_correct', 'order']
    list_filter   = ['is_correct']
    search_fields = ['text']