from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import AIGenerationRequest
from .serializers import GenerateQuizSerializer, GenerationStatusSerializer
from apps.quizzes.models import Topic
from apps.users.views import success_response, error_response
from services import ai_service


class GenerateQuizView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = GenerateQuizSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message='Validation failed',
                errors=serializer.errors
            )

        topic_id = serializer.validated_data['topic_id']

        try:
            topic = Topic.objects.get(id=topic_id, is_active=True)
        except Topic.DoesNotExist:
            return error_response(
                message='Topic not found',
                status_code=404
            )

        # create generation request
        ai_request = AIGenerationRequest.objects.create(
            requested_by=request.user,
            topic=topic,
            difficulty=serializer.validated_data['difficulty'],
            question_count=serializer.validated_data['question_count'],
            status='pending',
        )

        # run synchronously for now
        # in phase 2 this becomes: generate_quiz_task.delay(ai_request.id)
        ai_service.generate_quiz_questions(ai_request.id)

        # refresh from db
        ai_request.refresh_from_db()

        status_serializer = GenerationStatusSerializer(ai_request)

        if ai_request.status == 'completed':
            return success_response(
                data=status_serializer.data,
                message='Quiz generated successfully',
                status_code=201
            )
        else:
            return error_response(
                message=f'Generation failed: {ai_request.error_message}',
                errors=status_serializer.data,
                status_code=500
            )


class GenerationStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, request_id):
        try:
            ai_request = AIGenerationRequest.objects.select_related(
                'topic', 'quiz'
            ).get(id=request_id, requested_by=request.user)
        except AIGenerationRequest.DoesNotExist:
            return error_response(
                message='Generation request not found',
                status_code=404
            )

        serializer = GenerationStatusSerializer(ai_request)
        return success_response(data=serializer.data)


class GenerationHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        requests = AIGenerationRequest.objects.filter(
            requested_by=request.user
        ).select_related('topic', 'quiz').order_by('-created_at')

        serializer = GenerationStatusSerializer(requests, many=True)
        return success_response(data=serializer.data)