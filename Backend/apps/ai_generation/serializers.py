from rest_framework import serializers
from .models import AIGenerationRequest


class GenerateQuizSerializer(serializers.Serializer):
    topic_id       = serializers.IntegerField()
    difficulty     = serializers.ChoiceField(
                         choices=['easy', 'medium', 'hard']
                     )
    question_count = serializers.IntegerField(min_value=3, max_value=20)


class GenerationStatusSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    quiz_id    = serializers.IntegerField(
                     source='quiz.id',
                     read_only=True,
                     default=None
                 )

    class Meta:
        model  = AIGenerationRequest
        fields = [
            'id', 'topic_name', 'difficulty',
            'question_count', 'status',
            'error_message', 'retries',
            'quiz_id', 'created_at', 'completed_at'
        ]