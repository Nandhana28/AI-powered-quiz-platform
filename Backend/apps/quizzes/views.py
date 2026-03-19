from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from .serializers import (
    TopicSerializer,
    QuizListSerializer,
    QuizDetailSerializer,
    QuizCreateSerializer,
    QuestionCreateSerializer,
)
from services import quiz_service
from apps.users.views import success_response, error_response
from apps.users.permissions import IsAdminRole


class TopicListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        level = request.query_params.get('level')
        parent_id = request.query_params.get('parent')

        if parent_id:
            topics = quiz_service.get_topic_children(parent_id)
        else:
            from apps.quizzes.models import Topic
            topics = Topic.objects.filter(is_active=True)
            if level:
                topics = topics.filter(level=level)

        serializer = TopicSerializer(topics, many=True)
        return success_response(data=serializer.data)


class TopicDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, topic_id):
        topic = quiz_service.get_topic_by_id(topic_id)
        if not topic:
            return error_response(
                message='Topic not found',
                status_code=404
            )
        serializer = TopicSerializer(topic)
        return success_response(data=serializer.data)


class QuizListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        filters = {
            'topic_id':      request.query_params.get('topic'),
            'difficulty':    request.query_params.get('difficulty'),
        }
        quizzes = quiz_service.get_all_quizzes(filters)
        serializer = QuizListSerializer(quizzes, many=True)
        return success_response(data=serializer.data)

    def post(self, request):
        if not request.user.is_admin:
            return error_response(
                message='Only admins can create quizzes',
                status_code=403
            )
        serializer = QuizCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message='Validation failed',
                errors=serializer.errors
            )
        quiz = serializer.save(created_by=request.user)
        return success_response(
            data=QuizListSerializer(quiz).data,
            message='Quiz created successfully',
            status_code=201
        )


class QuizDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, quiz_id):
        quiz = quiz_service.get_quiz_with_questions(quiz_id)
        if not quiz:
            return error_response(
                message='Quiz not found',
                status_code=404
            )
        serializer = QuizDetailSerializer(quiz)
        return success_response(data=serializer.data)

    def patch(self, request, quiz_id):
        if not request.user.is_admin:
            return error_response(
                message='Only admins can update quizzes',
                status_code=403
            )
        quiz = quiz_service.get_quiz_by_id(quiz_id)
        if not quiz:
            return error_response(
                message='Quiz not found',
                status_code=404
            )
        quiz = quiz_service.update_quiz(quiz, request.data)
        return success_response(
            data=QuizListSerializer(quiz).data,
            message='Quiz updated successfully'
        )

    def delete(self, request, quiz_id):
        if not request.user.is_admin:
            return error_response(
                message='Only admins can delete quizzes',
                status_code=403
            )
        quiz = quiz_service.get_quiz_by_id(quiz_id)
        if not quiz:
            return error_response(
                message='Quiz not found',
                status_code=404
            )
        quiz_service.soft_delete_quiz(quiz)
        return success_response(message='Quiz deleted successfully')


class QuestionCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, quiz_id):
        if not request.user.is_admin:
            return error_response(
                message='Only admins can add questions',
                status_code=403
            )
        quiz = quiz_service.get_quiz_by_id(quiz_id)
        if not quiz:
            return error_response(
                message='Quiz not found',
                status_code=404
            )
        serializer = QuestionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message='Validation failed',
                errors=serializer.errors
            )
        question = quiz_service.add_question_to_quiz(
            quiz,
            serializer.validated_data
        )
        return success_response(
            data={'id': question.id, 'text': question.text},
            message='Question added successfully',
            status_code=201
        )