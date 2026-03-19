from rest_framework import serializers
from .models import QuizAttempt, AttemptAnswer
from apps.quizzes.serializers import QuestionWithAnswerSerializer


class StartAttemptSerializer(serializers.Serializer):
    quiz_id = serializers.IntegerField()


class AnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    choice_id   = serializers.IntegerField()


class AttemptStatusSerializer(serializers.ModelSerializer):
    quiz_title   = serializers.CharField(source='quiz.title', read_only=True)
    topic_name   = serializers.CharField(
                       source='quiz.topic.name',
                       read_only=True
                   )
    difficulty   = serializers.CharField(
                       source='quiz.difficulty',
                       read_only=True
                   )
    time_limit   = serializers.IntegerField(
                       source='quiz.time_limit_minutes',
                       read_only=True
                   )
    answers_count = serializers.SerializerMethodField()

    class Meta:
        model  = QuizAttempt
        fields = [
            'id', 'quiz_title', 'topic_name', 'difficulty',
            'status', 'time_limit', 'started_at',
            'expires_at', 'answers_count'
        ]

    def get_answers_count(self, obj):
        return obj.answers.count()


class AttemptAnswerResultSerializer(serializers.ModelSerializer):
    question_text    = serializers.CharField(
                           source='question.text',
                           read_only=True
                       )
    explanation      = serializers.CharField(
                           source='question.explanation',
                           read_only=True
                       )
    selected_text    = serializers.SerializerMethodField()
    correct_text     = serializers.SerializerMethodField()
    marks            = serializers.FloatField(
                           source='question.marks',
                           read_only=True
                       )

    class Meta:
        model  = AttemptAnswer
        fields = [
            'question_text', 'explanation',
            'selected_text', 'correct_text',
            'is_correct', 'marks_awarded', 'marks'
        ]

    def get_selected_text(self, obj):
        return obj.selected_choice.text if obj.selected_choice else 'Skipped'

    def get_correct_text(self, obj):
        correct = obj.question.choices.filter(is_correct=True).first()
        return correct.text if correct else ''


class AttemptResultSerializer(serializers.ModelSerializer):
    quiz_title      = serializers.CharField(source='quiz.title',      read_only=True)
    topic_name      = serializers.CharField(source='quiz.topic.name', read_only=True)
    difficulty      = serializers.CharField(source='quiz.difficulty', read_only=True)
    pass_percentage = serializers.FloatField(
                          source='quiz.pass_percentage',
                          read_only=True
                      )
    answers         = AttemptAnswerResultSerializer(many=True, read_only=True)

    class Meta:
        model  = QuizAttempt
        fields = [
            'id', 'quiz_title', 'topic_name', 'difficulty',
            'status', 'score', 'total_marks', 'percentage',
            'correct_count', 'incorrect_count', 'skipped_count',
            'is_passed', 'pass_percentage', 'xp_earned',
            'time_taken_seconds', 'is_late_submission',
            'started_at', 'submitted_at', 'answers'
        ]


class AttemptHistorySerializer(serializers.ModelSerializer):
    quiz_title = serializers.CharField(source='quiz.title',      read_only=True)
    topic_name = serializers.CharField(source='quiz.topic.name', read_only=True)
    difficulty = serializers.CharField(source='quiz.difficulty', read_only=True)

    class Meta:
        model  = QuizAttempt
        fields = [
            'id', 'quiz_title', 'topic_name', 'difficulty',
            'status', 'percentage', 'is_passed',
            'xp_earned', 'time_taken_seconds', 'started_at'
        ]