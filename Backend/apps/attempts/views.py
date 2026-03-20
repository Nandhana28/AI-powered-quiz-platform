from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .serializers import (
    StartAttemptSerializer,
    AnswerSerializer,
    AttemptStatusSerializer,
    AttemptResultSerializer,
    AttemptHistorySerializer,
)
from apps.attempts.models import QuizAttempt
from services import attempt_service
from apps.users.views import success_response, error_response


class StartAttemptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = StartAttemptSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message='Validation failed',
                errors=serializer.errors
            )

        attempt, error = attempt_service.start_attempt(
            user=request.user,
            quiz_id=serializer.validated_data['quiz_id']
        )

        if error:
            return error_response(message=error, status_code=404)

        # get questions without answers
        from apps.quizzes.serializers import QuestionSerializer
        questions = attempt.quiz.questions.filter(
            is_deleted=False
        ).prefetch_related('choices')

        return success_response(
            data={
                'attempt_id':  attempt.id,
                'quiz_title':  attempt.quiz.title,
                'difficulty':  attempt.quiz.difficulty,
                'time_limit':  attempt.quiz.time_limit_minutes,
                'expires_at':  attempt.expires_at,
                'total_questions': attempt.quiz.total_questions,
                'questions':   QuestionSerializer(
                                   questions, many=True
                               ).data,
            },
            message='Attempt started',
            status_code=201
        )


class AnswerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, attempt_id):
        try:
            attempt = QuizAttempt.objects.get(id=attempt_id)
        except QuizAttempt.DoesNotExist:
            return error_response(message='Attempt not found', status_code=404)

        # ownership check
        if not attempt_service.validate_attempt_ownership(
            attempt, request.user
        ):
            return error_response(
                message='Not your attempt',
                status_code=403
            )

        serializer = AnswerSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message='Validation failed',
                errors=serializer.errors
            )

        answer, error = attempt_service.save_answer(
            attempt=attempt,
            question_id=serializer.validated_data['question_id'],
            choice_id=serializer.validated_data['choice_id'],
        )

        if error:
            return error_response(message=error, status_code=400)

        return success_response(
            data={
                'question_id': answer.question_id,
                'is_correct':  answer.is_correct,
                'answers_saved': attempt.answers.count(),
            },
            message='Answer saved'
        )


class SubmitAttemptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, attempt_id):
        try:
            attempt = QuizAttempt.objects.select_related(
                'quiz__topic'
            ).get(id=attempt_id)
        except QuizAttempt.DoesNotExist:
            return error_response(message='Attempt not found', status_code=404)

        if not attempt_service.validate_attempt_ownership(
            attempt, request.user
        ):
            return error_response(
                message='Not your attempt',
                status_code=403
            )

        attempt, error = attempt_service.submit_attempt(attempt)

        if error:
            return error_response(message=error, status_code=400)

        # gamification
        from services import gamification_service, analytics_service, audit_service

        gamification_service.update_streak(request.user, attempt.quiz.difficulty)
        gamification_service.award_xp(request.user, attempt.xp_earned or 0)
        new_badges = gamification_service.check_and_award_badges(request.user, attempt)
        gamification_service.update_personal_best(
            user=request.user,
            topic=attempt.quiz.topic,
            difficulty=attempt.quiz.difficulty,
            score=attempt.percentage,
            attempt=attempt,
        )

        # analytics
        analytics_service.update_topic_stat(
            user=request.user,
            topic=attempt.quiz.topic,
            score=attempt.percentage,
            attempt=attempt,
        )
        percentile = analytics_service.calculate_percentile(
            request.user, attempt.quiz, attempt.percentage
        )
        suggestion = analytics_service.suggest_difficulty(
            request.user, attempt.quiz.topic
        )

        # audit
        audit_service.log_attempt_submitted(request.user, attempt)

        serializer = AttemptResultSerializer(attempt)
        data = serializer.data
        data['newly_earned_badges']    = new_badges
        data['percentile']             = percentile
        data['suggested_difficulty']   = suggestion

        return success_response(
            data=data,
            message='Quiz submitted successfully'
        )

class AttemptResultView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, attempt_id):
        try:
            attempt = QuizAttempt.objects.select_related(
                'quiz__topic'
            ).prefetch_related(
                'answers__question__choices',
                'answers__selected_choice'
            ).get(id=attempt_id)
        except QuizAttempt.DoesNotExist:
            return error_response(message='Attempt not found', status_code=404)

        if not attempt_service.validate_attempt_ownership(
            attempt, request.user
        ):
            return error_response(
                message='Not your attempt',
                status_code=403
            )

        if attempt.status == 'in_progress':
            return error_response(
                message='Attempt not yet submitted',
                status_code=400
            )

        serializer = AttemptResultSerializer(attempt)
        return success_response(data=serializer.data)


class AttemptHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        attempts = attempt_service.get_user_attempts(request.user)
        serializer = AttemptHistorySerializer(attempts, many=True)
        return success_response(data=serializer.data)