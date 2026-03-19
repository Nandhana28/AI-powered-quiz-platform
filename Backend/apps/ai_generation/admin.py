from django.contrib import admin
from .models import AIGenerationRequest


@admin.register(AIGenerationRequest)
class AIGenerationRequestAdmin(admin.ModelAdmin):
    list_display  = ['requested_by', 'topic', 'difficulty',
                     'question_count', 'status', 'retries', 'created_at']
    list_filter   = ['status', 'difficulty']
    search_fields = ['requested_by__email', 'topic__name']
    ordering      = ['-created_at']
    readonly_fields = ['raw_response', 'prompt_used']