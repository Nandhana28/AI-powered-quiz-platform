from rest_framework import serializers
from .models import Topic, Quiz, Question, Choice


class TopicSerializer(serializers.ModelSerializer):
    full_path    = serializers.CharField(
                       source='get_full_path',
                       read_only=True
                   )
    children_count = serializers.SerializerMethodField()

    class Meta:
        model  = Topic
        fields = [
            'id', 'name', 'slug', 'parent',
            'level', 'icon_key', 'is_active',
            'full_path', 'children_count'
        ]

    def get_children_count(self, obj):
        return obj.children.filter(is_active=True).count()


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Choice
        fields = ['id', 'text', 'order']
        # is_correct intentionally excluded — never sent during attempt


class ChoiceWithAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Choice
        fields = ['id', 'text', 'order', 'is_correct']
        # used only in results — after submission


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)

    class Meta:
        model  = Question
        fields = ['id', 'text', 'order', 'marks', 'choices']
        # explanation excluded during attempt — shown only in results


class QuestionWithAnswerSerializer(serializers.ModelSerializer):
    choices     = ChoiceWithAnswerSerializer(many=True, read_only=True)

    class Meta:
        model  = Question
        fields = [
            'id', 'text', 'order', 'marks',
            'explanation', 'choices'
        ]
        # full serializer — used in results page only


class QuizListSerializer(serializers.ModelSerializer):
    topic_name  = serializers.CharField(source='topic.name', read_only=True)
    topic_path  = serializers.CharField(
                      source='topic.get_full_path',
                      read_only=True
                  )
    created_by_email = serializers.CharField(
                           source='created_by.email',
                           read_only=True
                       )

    class Meta:
        model  = Quiz
        fields = [
            'id', 'title', 'description', 'topic_name',
            'topic_path', 'difficulty', 'total_questions',
            'time_limit_minutes', 'pass_percentage',
            'is_published', 'is_ai_generated',
            'created_by_email', 'created_at'
        ]


class QuizDetailSerializer(serializers.ModelSerializer):
    topic       = TopicSerializer(read_only=True)
    questions   = QuestionSerializer(many=True, read_only=True)
    created_by_email = serializers.CharField(
                           source='created_by.email',
                           read_only=True
                       )

    class Meta:
        model  = Quiz
        fields = [
            'id', 'title', 'description', 'topic',
            'difficulty', 'total_questions',
            'time_limit_minutes', 'pass_percentage',
            'instructions', 'is_published', 'is_ai_generated',
            'available_from', 'expires_at',
            'created_by_email', 'created_at', 'updated_at',
            'questions'
        ]


class QuizCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Quiz
        fields = [
            'title', 'description', 'topic',
            'difficulty', 'total_questions',
            'time_limit_minutes', 'pass_percentage',
            'instructions', 'is_published',
            'available_from', 'expires_at'
        ]


class ChoiceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Choice
        fields = ['text', 'is_correct', 'order']


class QuestionCreateSerializer(serializers.ModelSerializer):
    choices = ChoiceCreateSerializer(many=True)

    class Meta:
        model  = Question
        fields = ['text', 'explanation', 'order', 'marks', 'choices']

    def validate_choices(self, choices):
        correct = [c for c in choices if c.get('is_correct')]
        if len(correct) != 1:
            raise serializers.ValidationError(
                'Each question must have exactly one correct choice.'
            )
        if len(choices) < 2:
            raise serializers.ValidationError(
                'Each question must have at least 2 choices.'
            )
        return choices